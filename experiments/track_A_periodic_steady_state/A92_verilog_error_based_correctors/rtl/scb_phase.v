`timescale 1ns / 1ps
// One SCB phase: HIGH -> DOWN -> LOW -> UP -> HIGH, in mode S (fixed timing, start-up) or mode P.
//
// A92 version of A89's scb_phase (A89's copy is unchanged). Addition (BOUNDARY Section 3): error-based
//   updates of the two correctors, each opt-in. The reports carry the signed timing error of the actual edge
//   (APEC 2023's phase error detector): ml_err = actual low-side turn-on - zero crossing, m_err = actual
//   high-side turn-on - valley (LSB, reported when the edge was not early). With cfg_err_low the late/at rule
//   becomes dtl -= (ml_err - cfg_el_tgt) >>> cfg_err_shift; with cfg_err_high, dt_pred = base -
//   ((m_err - cfg_eh_tgt) >>> cfg_err_shift), base being the delay the phase used (dt_pred, or cfg_rs_high
//   after a restart turn-on). Both are clamped to [0, max]. Early and flat rules are A89's. With both bits 0
//   every path is A89's.
//
// A89 version of A81's scb_phase (A81's copy is unchanged). Addition (cfg_low_pred, mode P): the low side
//   turns on at t_off + dtl, a timed edge (chained with the high-side turn-off when both fall in one window),
//   instead of at the synchronised zero-voltage comparator. dtl is corrected by a zero-crossing report
//   (ml_valid, ml_early, ml_tv): early -> dtl + cfg_dtl_step, otherwise dtl = ml_tv, both capped at
//   cfg_dtl_max (the A88 rule). With cfg_low_pred = 0 every path is A81's.
//   Leading-edge blanking (cfg_blank, BOUNDARY Section 8): phase 1's current comparators (the asynchronous
//   arm and the synchronous c_i) act only once now - t_lon >= cfg_blank, t_lon being the low-side turn-on
//   command. The timed low side enters LOW a driver delay before the physical turn-off; without blanking the
//   front end can fire while the physical high side still conducts. cfg_blank = 0: always open (A81).
//
// A81 version of A80's scb_phase (A80's copy is unchanged). Addition (cfg_async, phase 1 in mode P):
//   phase 1's current-decided low-side turn-off and the predictive high-side turn-on after it are made by
//   the asynchronous front end (armed comparator -> latch -> gate; latch -> delay line dt_pred -> gate).
//   The logic raises arm while waiting, emits no gate event for those two edges, and on the front end's
//   TDC report (a_valid, a_tlo) records t_lo = a_tlo and t_on = a_tlo + dt_pred and enters HIGH.
//   The phase-1 restart stays on the clocked path.
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
    input  wire                 cfg_async,     // A81: phase 1 turn-off/turn-on by the asynchronous front end
    input  wire                 a_valid,       // A81: TDC report of the asynchronous turn-off (one-cycle pulse)
    input  wire [TW-1:0]        a_tlo,         // A81: its command-equivalent time, LSB
    input  wire                 cfg_low_pred,  // A89: timed low-side turn-on in mode P
    input  wire [TW-1:0]        dtl_init,      // A89: initial low-side dead time, LSB
    input  wire [TW-1:0]        cfg_dtl_step,  // A89: early step, LSB
    input  wire [TW-1:0]        cfg_dtl_max,   // A89: cap, LSB
    input  wire                 ml_valid,      // A89: zero-crossing report (one-cycle pulse)
    input  wire                 ml_early,      // A89: the node had not crossed zero at the edge
    input  wire [TW-1:0]        ml_tv,         // A89: crossing time after the high-side turn-off, LSB
    input  wire [TW-1:0]        cfg_blank,     // A89: current-comparator blanking after the low-side turn-on, LSB
    input  wire                 cfg_err_low,   // A92: error-based low-side update
    input  wire                 cfg_err_high,  // A92: error-based high-side update
    input  wire [TW-1:0]        cfg_el_tgt,    // A92: low-side error target, LSB
    input  wire [TW-1:0]        cfg_eh_tgt,    // A92: high-side error target, LSB
    input  wire [3:0]           cfg_err_shift, // A92: gain 2^-shift
    input  wire [TW-1:0]        ml_err,        // A92: actual low-side turn-on - zero crossing, LSB
    input  wire [TW-1:0]        m_err,         // A92: actual high-side turn-on - valley, LSB
    output wire                 arm,           // A81: front end armed (phase 1 LOW in mode P)
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
    output reg  [15:0]          late_fires,
    output reg  [TW-1:0]        dtl            // A89: low-side dead time, LSB
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
    wire async_on   = FIRST && cfg_async && mode_p;
    wire lo_open    = $signed(now - t_lon) >= $signed(cfg_blank);   // A89: blanking elapsed
    assign arm = async_on && (state == LOW) && lo_open;
    wire slot_new   = (fired_ref != ref_id);
    wire [TW-1:0] dt_next = dt_pred + cfg_dt_step;
    // A89: timed low side. The chained target counts from the placed turn-off (window start + f_off).
    wire lp_on = mode_p && cfg_low_pred;
    wire signed [TW-1:0] d_lpred = t_off + dtl - now;
    wire signed [TW-1:0] d_off_l = {{(TW - FB){1'b0}}, f_off} + dtl;
    wire [FB-1:0] f_lpred = fine(d_lpred, cfg_fine);
    wire [FB-1:0] f_off_l = fine(d_off_l, cfg_fine);
    wire [TW-1:0] dtl_next = dtl + cfg_dtl_step;
    // A92: error-based updates, in signed arithmetic two bits wider than TW, clamped to [0, max]
    wire signed [TW+1:0] el_d    = ($signed({2'b00, ml_err}) - $signed({2'b00, cfg_el_tgt})) >>> cfg_err_shift;
    wire signed [TW+1:0] dtl_e   = $signed({2'b00, dtl}) - el_d;
    wire [TW-1:0]        dtl_err = dtl_e[TW+1] ? {TW{1'b0}} :
                                   (dtl_e > $signed({2'b00, cfg_dtl_max})) ? cfg_dtl_max : dtl_e[TW-1:0];
    wire [TW-1:0]        eh_base = (on_how == HOW_RESTART) ? cfg_rs_high : dt_pred;
    wire signed [TW+1:0] eh_d    = ($signed({2'b00, m_err}) - $signed({2'b00, cfg_eh_tgt})) >>> cfg_err_shift;
    wire signed [TW+1:0] dtp_e   = $signed({2'b00, eh_base}) - eh_d;
    wire [TW-1:0]        dtp_err = dtp_e[TW+1] ? {TW{1'b0}} :
                                   (dtp_e > $signed({2'b00, cfg_dt_max})) ? cfg_dt_max : dtp_e[TW-1:0];

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
            dtl         <= dtl_init;
        end else begin
            if (m_valid) begin
                if (m_early)
                    dt_pred <= (dt_next > cfg_dt_max) ? cfg_dt_max : dt_next;
                else if (!m_flat)
                    dt_pred <= cfg_err_high ? dtp_err : m_tv;          // A92: error-based when set
            end
            if (ml_valid && cfg_low_pred) begin                  // A89: zero-crossing correction
                if (ml_early)
                    dtl <= (dtl_next > cfg_dtl_max) ? cfg_dtl_max : dtl_next;
                else if (cfg_err_low)                            // A92: error-based
                    dtl <= dtl_err;
                else
                    dtl <= (ml_tv > cfg_dtl_max) ? cfg_dtl_max : ml_tv;
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
                        end else if (lp_on && due(d_off_l)) begin // A89: timed low side in the same window
                            gl_ev <= 1'b1; gl_lvl <= 1'b1; gl_fine <= f_off_l;
                            t_lon <= now + f_off_l;
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
                    end else if (lp_on) begin                     // A89: timed low side (restart as guard)
                        if (due(d_lpred)) begin
                            gl_ev <= 1'b1; gl_lvl <= 1'b1; gl_fine <= f_lpred;
                            t_lon <= now + f_lpred;
                            if (d_lpred[TW-1]) late_fires <= late_fires + 1'b1;
                            state <= LOW;
                        end else if (due(d_rsd)) begin
                            gl_ev <= 1'b1; gl_lvl <= 1'b1; gl_fine <= f_rsd;
                            t_lon <= now + f_rsd;
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
                    end else if (async_on) begin
                        if (a_valid) begin                       // A81: edges made by the front end
                            t_lo <= a_tlo; lo_bind_cur <= 1'b1; lo_pulse <= 1'b1;
                            t_on <= a_tlo + dt_pred; on_how <= HOW_PRED; on_pulse <= 1'b1;
                            state <= HIGH;
                        end else if (due(d_rs1)) begin
                            gl_ev <= 1'b1; gl_lvl <= 1'b0; gl_fine <= f_rs1;
                            t_lo <= now + f_rs1; lo_bind_cur <= 1'b0; lo_pulse <= 1'b1;
                            state <= UP;
                        end
                    end else if (FIRST) begin
                        if (c_i && lo_open) begin                // A89: blanking
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
