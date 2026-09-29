`timescale 1ns / 1ps
// One SCB phase: HIGH -> DOWN -> LOW -> UP -> HIGH, in mode S (fixed timing, start-up) or mode P.
//
// A80 version of A77's scb_phase (A77's copy is unchanged). Changes:
//   - mode S (the A71/A73 start-up timing): low side on at t_off + t_dead; phase 1's low side off
//     at t_on + T0 - t_dead; phases 2..N at their slots; high side on at t_lo + t_dead.
//     No comparator, no restart, no measurement in mode S.
//   - Two timed transitions that fall in the same window are emitted together. The mode-S dead
//     time (2.15 ns) is shorter than a 4 ns clock, so off -> on across the dead time must not wait
//     for the next clock.
//   - Ton comes in as an input (configuration or voltage loop).
//
// Time is in LSB units (1 LSB = T_clk / 2^FB); each clock handles the window [now, now + 2^FB).
// A timed edge in the window carries its fine offset; a comparator-decided edge is at the window
// start. Recorded edge times are the placed ones.
module scb_phase #(
    parameter TW    = 32,
    parameter FB    = 5,
    parameter CW    = 8,
    parameter FIRST = 0
) (
    input  wire                 clk,
    input  wire                 rst,
    input  wire [TW-1:0]        now,
    input  wire                 mode_p,        // 0: mode S (fixed timing), 1: mode P
    input  wire [TW-1:0]        ton,           // current on-time
    input  wire [TW-1:0]        cfg_t0,        // mode S period
    input  wire [TW-1:0]        cfg_tdead,     // mode S dead time
    input  wire [TW-1:0]        cfg_rs_high,
    input  wire [TW-1:0]        cfg_rs_low,
    input  wire [TW-1:0]        cfg_dt_step,
    input  wire [TW-1:0]        cfg_dt_max,
    input  wire                 cfg_pred,
    input  wire                 cfg_zvs_react,
    input  wire                 cfg_trim,
    input  wire                 cfg_fine,
    input  wire [TW-1:0]        dt_init,
    input  wire signed [CW-1:0] trim_init,
    input  wire [TW-1:0]        slot_time,
    input  wire [TW-1:0]        ref_id,
    input  wire                 c_i,
    input  wire                 c_zl,
    input  wire                 c_zh,
    input  wire                 c_valley,
    input  wire                 m_valid,
    input  wire                 m_early,
    input  wire                 m_flat,
    input  wire [TW-1:0]        m_tv,
    input  wire                 r_valid,
    input  wire                 r_below,
    output reg                  gh_ev,
    output reg                  gh_lvl,
    output reg  [FB-1:0]        gh_fine,
    output reg                  gl_ev,
    output reg                  gl_lvl,
    output reg  [FB-1:0]        gl_fine,
    output reg  [1:0]           state,
    output reg  [TW-1:0]        t_on,
    output reg                  on_pulse,
    output reg  [2:0]           on_how,        // 0 predictive, 1 valley, 2 ZVS, 3 restart, 4 timed (mode S)
    output reg                  lo_pulse,
    output reg                  lo_bind_cur,
    output reg  signed [CW-1:0] trim,
    output reg  [TW-1:0]        dt_pred,
    output reg  [15:0]          late_fires
);
    localparam [1:0] HIGH = 2'd0, DOWN = 2'd1, LOW = 2'd2, UP = 2'd3;
    localparam [2:0] HOW_PRED = 3'd0, HOW_VALLEY = 3'd1, HOW_ZVS = 3'd2, HOW_RESTART = 3'd3, HOW_TIMED = 3'd4;
    localparam signed [TW-1:0] WIN = 1 << FB;
    localparam signed [CW-1:0] TRIM_MAX = (1 << (CW - 1)) - 1;
    localparam signed [CW-1:0] TRIM_MIN = -(1 << (CW - 1));

    reg [TW-1:0] t_off, t_lon, t_lo, fired_ref;

    wire signed [TW-1:0] d_off   = t_on + ton - now;
    wire signed [TW-1:0] d_rsd   = t_off + cfg_rs_high - now;
    wire signed [TW-1:0] d_rs1   = t_lon + cfg_rs_low - now;
    wire signed [TW-1:0] d_slot  = slot_time - now;
    wire signed [TW-1:0] d_pred  = t_lo + dt_pred - now;
    wire signed [TW-1:0] d_rsu   = t_lo + cfg_rs_high - now;
    // mode S
    wire signed [TW-1:0] d_lon_s = t_off + cfg_tdead - now;          // DOWN: low side on
    wire signed [TW-1:0] d_lo1_s = t_on + cfg_t0 - cfg_tdead - now;  // phase 1 LOW: low side off
    wire signed [TW-1:0] d_hon_s = t_lo + cfg_tdead - now;           // UP: high side on
    // mode S chained targets: the second edge of a pair, one dead time after the first
    wire signed [TW-1:0] d_off_c = d_off + cfg_tdead;
    wire signed [TW-1:0] d_lo_s  = FIRST ? d_lo1_s : d_slot;
    wire signed [TW-1:0] d_lo_c  = d_lo_s + cfg_tdead;

    function due;
        input signed [TW-1:0] d;
        due = (d < WIN);
    endfunction

    function [FB-1:0] fine;
        input signed [TW-1:0] d;
        input en;
        fine = (d[TW-1] || !en) ? {FB{1'b0}} : d[FB-1:0];
    endfunction

    wire [FB-1:0] f_off   = fine(d_off, cfg_fine);
    wire [FB-1:0] f_off_c = fine(d_off_c, cfg_fine);
    wire [FB-1:0] f_rsd   = fine(d_rsd, cfg_fine);
    wire [FB-1:0] f_rs1   = fine(d_rs1, cfg_fine);
    wire [FB-1:0] f_slot  = fine(d_slot, cfg_fine);
    wire [FB-1:0] f_pred  = fine(d_pred, cfg_fine);
    wire [FB-1:0] f_rsu   = fine(d_rsu, cfg_fine);
    wire [FB-1:0] f_lon_s = fine(d_lon_s, cfg_fine);
    wire [FB-1:0] f_lo_s  = fine(d_lo_s, cfg_fine);
    wire [FB-1:0] f_lo_c  = fine(d_lo_c, cfg_fine);
    wire [FB-1:0] f_hon_s = fine(d_hon_s, cfg_fine);

    wire pred_first = due(d_pred) && !(due(d_rsu) && (d_rsu < d_pred));
    wire slot_new   = (fired_ref != ref_id);
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
            on_how      <= HOW_TIMED;
            lo_bind_cur <= 1'b0;
            trim        <= trim_init;
            dt_pred     <= dt_init;
            late_fires  <= 16'd0;
        end else begin
            if (m_valid) begin
                if (m_early)
                    dt_pred <= (dt_next > cfg_dt_max) ? cfg_dt_max : dt_next;
                else if (!m_flat)
                    dt_pred <= m_tv;
            end
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
                        if (!mode_p && due(d_off_c)) begin      // mode S: low side on in the same window
                            gl_ev <= 1'b1; gl_lvl <= 1'b1; gl_fine <= f_off_c;
                            t_lon <= now + f_off_c;
                            state <= LOW;
                        end else begin
                            state <= DOWN;
                        end
                    end
                end
                DOWN: begin
                    if (!mode_p) begin
                        if (due(d_lon_s)) begin
                            gl_ev <= 1'b1; gl_lvl <= 1'b1; gl_fine <= f_lon_s;
                            t_lon <= now + f_lon_s;
                            state <= LOW;
                        end
                    end else if (c_zl) begin
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
                    if (!mode_p) begin
                        // mode S: phase 1 at t_on + T0 - t_dead, phases 2..N at their slots
                        if ((FIRST || slot_new) && due(d_lo_s)) begin
                            gl_ev <= 1'b1; gl_lvl <= 1'b0; gl_fine <= f_lo_s;
                            t_lo <= now + f_lo_s; lo_bind_cur <= 1'b0; lo_pulse <= 1'b1;
                            if (!FIRST) fired_ref <= ref_id;
                            if (d_lo_s[TW-1]) late_fires <= late_fires + 1'b1;
                            if (due(d_lo_c)) begin               // high side on in the same window
                                gh_ev <= 1'b1; gh_lvl <= 1'b1; gh_fine <= f_lo_c;
                                t_on <= now + f_lo_c; on_how <= HOW_TIMED; on_pulse <= 1'b1;
                                state <= HIGH;
                            end else begin
                                state <= UP;
                            end
                        end
                    end else if (FIRST) begin
                        if (c_i) begin
                            gl_ev <= 1'b1; gl_lvl <= 1'b0; gl_fine <= {FB{1'b0}};
                            t_lo <= now; lo_bind_cur <= 1'b1; lo_pulse <= 1'b1;
                            state <= UP;
                        end else if (due(d_rs1)) begin
                            gl_ev <= 1'b1; gl_lvl <= 1'b0; gl_fine <= f_rs1;
                            t_lo <= now + f_rs1; lo_bind_cur <= 1'b0; lo_pulse <= 1'b1;
                            state <= UP;
                        end
                    end else if (slot_new && due(d_slot)) begin
                        gl_ev <= 1'b1; gl_lvl <= 1'b0; gl_fine <= f_slot;
                        t_lo <= now + f_slot; lo_bind_cur <= 1'b0; lo_pulse <= 1'b1;
                        fired_ref <= ref_id;
                        if (d_slot[TW-1]) late_fires <= late_fires + 1'b1;
                        state <= UP;
                    end
                end
                UP: begin
                    if (!mode_p) begin
                        if (due(d_hon_s)) begin
                            gh_ev <= 1'b1; gh_lvl <= 1'b1; gh_fine <= f_hon_s;
                            t_on <= now + f_hon_s; on_how <= HOW_TIMED; on_pulse <= 1'b1;
                            state <= HIGH;
                        end
                    end else if (cfg_zvs_react && c_zh) begin
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
