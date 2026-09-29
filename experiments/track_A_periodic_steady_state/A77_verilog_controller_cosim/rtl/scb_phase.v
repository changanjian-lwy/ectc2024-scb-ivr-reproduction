`timescale 1ns / 1ps
// One SCB phase in mode P: HIGH -> DOWN -> LOW -> UP -> HIGH, the A69-A76 state machine.
//
// Time is counted in LSB units, 1 LSB = T_clk / 2^FB. Each clock handles the window
// [now, now + 2^FB).
//   - A timed transition whose target lies in the window is emitted with its fine offset;
//     the external delay line places the edge.
//   - A comparator-decided transition is emitted at the window start (fine 0).
//   - A timed target already in the past is emitted at once and counted in late_fires.
//   - The recorded edge times are the placed ones, so quantisation does not accumulate.
//
// Rules adopted in A76:
//   - predictive valley turn-on with per-cycle correction (A75);
//   - sign-based comparator trim (Schaef et al., ISSCC 2019);
//   - restart timers on every wait;
//   - reactive ZVS off by default (cfg_zvs_react).
// Reset: phase 1 (FIRST) HIGH from t = 0; phases 2..N LOW, waiting for their slots.
module scb_phase #(
    parameter TW    = 32,  // time width, LSB units
    parameter FB    = 5,   // fine (delay-line) bits
    parameter CW    = 8,   // comparator trim code width, signed
    parameter FIRST = 0    // 1: phase 1 (current-decided turn-off; its turn-on sets t_ref)
) (
    input  wire                 clk,
    input  wire                 rst,
    input  wire [TW-1:0]        now,
    // configuration, LSB units
    input  wire [TW-1:0]        cfg_ton,
    input  wire [TW-1:0]        cfg_rs_high,   // restart after a high-side (DOWN) or low-side (UP) turn-off
    input  wire [TW-1:0]        cfg_rs_low,    // phase 1: restart of the current-target wait
    input  wire [TW-1:0]        cfg_dt_step,   // predictive correction step when early
    input  wire [TW-1:0]        cfg_dt_max,
    input  wire                 cfg_pred,      // 1: predictive valley turn-on, 0: reactive valley
    input  wire                 cfg_zvs_react, // reactive high-side ZVS decision
    input  wire                 cfg_trim,      // comparator self-trim
    input  wire                 cfg_fine,      // 0: counter-only DPWM (fine offset forced to 0)
    input  wire [TW-1:0]        dt_init,
    input  wire signed [CW-1:0] trim_init,
    // phases 2..N: this cycle's turn-off slot; ref_id changes once per phase-1 cycle
    input  wire [TW-1:0]        slot_time,
    input  wire [TW-1:0]        ref_id,
    // synchronised comparators
    input  wire                 c_i,           // i_k <= theta_k
    input  wire                 c_zl,          // Vds(SL_k) <= 0
    input  wire                 c_zh,          // Vds(SH_k) <= 0
    input  wire                 c_valley,      // reactive valley detector
    // measurement after a predictive turn-on (one-cycle pulse)
    input  wire                 m_valid,
    input  wire                 m_early,       // node still falling at the edge
    input  wire                 m_flat,        // no ring seen
    input  wire [TW-1:0]        m_tv,          // valley time after the low-side turn-off
    // residual-current sign after a current-decided turn-off (one-cycle pulse)
    input  wire                 r_valid,
    input  wire                 r_below,       // edge current below target: trip later next time
    // gate edge requests
    output reg                  gh_ev,
    output reg                  gh_lvl,
    output reg  [FB-1:0]        gh_fine,
    output reg                  gl_ev,
    output reg                  gl_lvl,
    output reg  [FB-1:0]        gl_fine,
    // status
    output reg  [1:0]           state,
    output reg  [TW-1:0]        t_on,          // placed time of the last high-side turn-on
    output reg                  on_pulse,
    output reg  [1:0]           on_how,        // 0 predictive, 1 valley, 2 ZVS, 3 restart
    output reg                  lo_pulse,
    output reg                  lo_bind_cur,   // last low-side turn-off decided by the current comparator
    output reg  signed [CW-1:0] trim,
    output reg  [TW-1:0]        dt_pred,
    output reg  [15:0]          late_fires
);
    localparam [1:0] HIGH = 2'd0, DOWN = 2'd1, LOW = 2'd2, UP = 2'd3;
    localparam [1:0] HOW_PRED = 2'd0, HOW_VALLEY = 2'd1, HOW_ZVS = 2'd2, HOW_RESTART = 2'd3;
    localparam signed [TW-1:0] WIN = 1 << FB;
    localparam signed [CW-1:0] TRIM_MAX = (1 << (CW - 1)) - 1;
    localparam signed [CW-1:0] TRIM_MIN = -(1 << (CW - 1));

    reg [TW-1:0] t_off, t_lon, t_lo, fired_ref;

    // Signed distance from the window start to each timed target.
    wire signed [TW-1:0] d_off  = t_on + cfg_ton - now;
    wire signed [TW-1:0] d_rsd  = t_off + cfg_rs_high - now;
    wire signed [TW-1:0] d_rs1  = t_lon + cfg_rs_low - now;
    wire signed [TW-1:0] d_slot = slot_time - now;
    wire signed [TW-1:0] d_pred = t_lo + dt_pred - now;
    wire signed [TW-1:0] d_rsu  = t_lo + cfg_rs_high - now;

    function due;
        input signed [TW-1:0] d;
        due = (d < WIN);
    endfunction

    function [FB-1:0] fine;
        input signed [TW-1:0] d;
        input en;
        fine = (d[TW-1] || !en) ? {FB{1'b0}} : d[FB-1:0];
    endfunction

    wire [FB-1:0] f_off  = fine(d_off, cfg_fine);
    wire [FB-1:0] f_rsd  = fine(d_rsd, cfg_fine);
    wire [FB-1:0] f_rs1  = fine(d_rs1, cfg_fine);
    wire [FB-1:0] f_slot = fine(d_slot, cfg_fine);
    wire [FB-1:0] f_pred = fine(d_pred, cfg_fine);
    wire [FB-1:0] f_rsu  = fine(d_rsu, cfg_fine);

    // The predictive edge wins unless the restart is due earlier in the same window.
    wire pred_first = due(d_pred) && !(due(d_rsu) && (d_rsu < d_pred));
    wire [TW-1:0] dt_next = dt_pred + cfg_dt_step;

    always @(posedge clk) begin
        gh_ev    <= 1'b0;
        gl_ev    <= 1'b0;
        on_pulse <= 1'b0;
        lo_pulse <= 1'b0;
        if (rst) begin
            state       <= FIRST ? HIGH : LOW;
            t_on        <= {TW{1'b0}};
            t_off       <= {TW{1'b0}};
            t_lon       <= {TW{1'b0}};
            t_lo        <= {TW{1'b0}};
            fired_ref   <= {TW{1'b1}};
            gh_lvl      <= FIRST ? 1'b1 : 1'b0;
            gl_lvl      <= FIRST ? 1'b0 : 1'b1;
            gh_fine     <= {FB{1'b0}};
            gl_fine     <= {FB{1'b0}};
            on_how      <= HOW_PRED;
            lo_bind_cur <= 1'b0;
            trim        <= trim_init;
            dt_pred     <= dt_init;
            late_fires  <= 16'd0;
        end else begin
            // A75's predictive correction, from the measurement after a predictive turn-on.
            if (m_valid) begin
                if (m_early)
                    dt_pred <= (dt_next > cfg_dt_max) ? cfg_dt_max : dt_next;
                else if (!m_flat)
                    dt_pred <= m_tv;
            end
            // Schaef-style sign-based trim after a current-decided turn-off.
            if (r_valid && cfg_trim && lo_bind_cur) begin
                if (r_below && trim != TRIM_MAX)
                    trim <= trim + 1'b1;
                else if (!r_below && trim != TRIM_MIN)
                    trim <= trim - 1'b1;
            end

            case (state)
                HIGH: begin
                    if (due(d_off)) begin
                        gh_ev <= 1'b1; gh_lvl <= 1'b0; gh_fine <= f_off;
                        t_off <= now + f_off;
                        if (d_off[TW-1]) late_fires <= late_fires + 1'b1;
                        state <= DOWN;
                    end
                end
                DOWN: begin
                    if (c_zl) begin
                        gl_ev <= 1'b1; gl_lvl <= 1'b1; gl_fine <= {FB{1'b0}};
                        t_lon <= now;
                        state <= LOW;
                    end else if (due(d_rsd)) begin
                        gl_ev <= 1'b1; gl_lvl <= 1'b1; gl_fine <= f_rsd;
                        t_lon <= now + f_rsd;
                        state <= LOW;
                    end
                end
                LOW: begin
                    if (FIRST) begin
                        if (c_i) begin
                            gl_ev <= 1'b1; gl_lvl <= 1'b0; gl_fine <= {FB{1'b0}};
                            t_lo <= now; lo_bind_cur <= 1'b1; lo_pulse <= 1'b1;
                            state <= UP;
                        end else if (due(d_rs1)) begin
                            gl_ev <= 1'b1; gl_lvl <= 1'b0; gl_fine <= f_rs1;
                            t_lo <= now + f_rs1; lo_bind_cur <= 1'b0; lo_pulse <= 1'b1;
                            state <= UP;
                        end
                    end else if (fired_ref != ref_id && due(d_slot)) begin
                        gl_ev <= 1'b1; gl_lvl <= 1'b0; gl_fine <= f_slot;
                        t_lo <= now + f_slot; lo_bind_cur <= 1'b0; lo_pulse <= 1'b1;
                        fired_ref <= ref_id;
                        if (d_slot[TW-1]) late_fires <= late_fires + 1'b1;
                        state <= UP;
                    end
                end
                UP: begin
                    if (cfg_zvs_react && c_zh) begin
                        gh_ev <= 1'b1; gh_lvl <= 1'b1; gh_fine <= {FB{1'b0}};
                        t_on <= now; on_how <= HOW_ZVS; on_pulse <= 1'b1;
                        state <= HIGH;
                    end else if (cfg_pred && pred_first) begin
                        gh_ev <= 1'b1; gh_lvl <= 1'b1; gh_fine <= f_pred;
                        t_on <= now + f_pred; on_how <= HOW_PRED; on_pulse <= 1'b1;
                        if (d_pred[TW-1]) late_fires <= late_fires + 1'b1;
                        state <= HIGH;
                    end else if (!cfg_pred && c_valley) begin
                        gh_ev <= 1'b1; gh_lvl <= 1'b1; gh_fine <= {FB{1'b0}};
                        t_on <= now; on_how <= HOW_VALLEY; on_pulse <= 1'b1;
                        state <= HIGH;
                    end else if (due(d_rsu)) begin
                        gh_ev <= 1'b1; gh_lvl <= 1'b1; gh_fine <= f_rsu;
                        t_on <= now + f_rsu; on_how <= HOW_RESTART; on_pulse <= 1'b1;
                        state <= HIGH;
                    end
                end
            endcase
        end
    end
endmodule
