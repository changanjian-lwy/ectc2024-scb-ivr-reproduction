`timescale 1ns / 1ps
// One SCB phase controller, states HIGH -> DOWN -> LOW -> UP -> HIGH, in mode S (start-up) or mode P.
//
// Time is in LSB units (1 LSB = T_clk / 2^FB); each clock handles the window [now, now + 2^FB). A timed edge in the
// window carries its fine offset; a comparator-decided edge is at the window start. Recorded edge times are the
// placed ones. Two timed transitions that fall in one window are emitted together (chained).
//
// Mode S (fixed timing, no comparator, restart or measurement): low side on at t_off + cfg_tdead; phase 1's low side
// off at t_on + cfg_t0 - cfg_tdead, phases 2..N at their slots; high side on at t_lo + cfg_tdead.
//
// Mode P:
// - high-side turn-off at t_on + ton;
// - low-side turn-on: at the synchronised V_DS = 0 comparator, or with cfg_low_pred timed at t_off + dtl (chained
//   into the turn-off window when it falls there); the restart timer cfg_rs_high is the guard;
// - low-side turn-off: phase 1 at the synchronised current comparator, acting only once now - t_lon >= cfg_blank,
//   or with cfg_async by the asynchronous front end (arm -> external latch and gate edges; the TDC report a_valid /
//   a_tlo records t_lo and t_on = a_tlo + dt_pred); restart timer cfg_rs_low. With cfg_lo_pred (phase 1), each
//   comparator-decided turn-off sets dlo to its on-low interval (t_lo - t_lon), and after cfg_lo_learn of them the
//   turn-off is a timed edge at t_lon + dlo (lo_timed; the front end is not armed), followed by the predictive
//   turn-on; dlo then steps +1 when the crossing report is early or below cfg_lo_tgt, else -1 (A100: with cfg_lo_adm
//   the step doubles while consecutive decisions agree, up to cfg_lo_smax, and returns to 1 when they differ; with
//   cfg_lo_ff, dlo also moves by cfg_lo_kff times every change of ton). Phases 2..N at their slot
//   (slot_time from scb_ctrl); with cfg_slot_guard a slot not yet fired when the reference changes fires at once
//   (fine 0, a late fire) and counts as the new reference's slot;
// - high-side turn-on: predictive at t_lo + dt_pred (cfg_pred), else at the valley comparator, or reactive ZVS
//   (cfg_zvs_react); restart timer cfg_rs_high.
//
// Correctors (one report per edge):
// - dt_pred: early -> + cfg_dt_step (capped at cfg_dt_max); flat -> hold; otherwise the measured valley time m_tv, or
//   with cfg_err_high base - ((m_err - cfg_eh_tgt) >>> cfg_err_shift) clamped to [0, cfg_dt_max], base = dt_pred,
//   or cfg_rs_high after a restart turn-on;
// - dtl (cfg_low_pred): early -> + cfg_dtl_step; otherwise the measured crossing time ml_tv, or with cfg_err_low
//   dtl - ((ml_err - cfg_el_tgt) >>> cfg_err_shift); both clamped to [0, cfg_dtl_max];
// - trim: +1 / -1 per current-decided low-side turn-off from the residual-current sign (cfg_trim).
//
// Every option bit at 0 gives the original behaviour of each path. From A93's rtl (history: CHANGELOG.md).
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
    input  wire                 cfg_slot_guard,// A93: fire a missed slot when the reference changes
    input  wire                 cfg_lo_pred,   // A99: timed phase-1 low-side turn-off after learning
    input  wire [15:0]          cfg_lo_learn,  // A99: comparator-decided mode-P turn-offs before it
    input  wire [TW-1:0]        cfg_lo_tgt,    // A99: target of actual turn-off - crossing, LSB
    input  wire                 mlo_valid,     // A99: crossing report at the timed turn-off (one-cycle pulse)
    input  wire                 mlo_early,     // A99: the current had not reached the target at the turn-off
    input  wire [TW-1:0]        mlo_err,       // A99: actual turn-off - crossing, LSB
    input  wire                 cfg_lo_adm,    // A100: adaptive step (doubling while decisions agree)
    input  wire [7:0]           cfg_lo_smax,   // A100: its largest step, LSB
    input  wire                 cfg_lo_ff,     // A100: Ton feedforward
    input  wire [7:0]           cfg_lo_kff,    // A100: dlo change per LSB of ton
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
    output reg  [TW-1:0]        dtl,           // A89: low-side dead time, LSB
    output reg  [TW-1:0]        dlo,           // A99: phase 1's on-low interval for the timed turn-off, LSB
    output wire                 lo_timed       // A99: phase 1's turn-off is timed
);
    localparam [1:0] HIGH = 2'd0, DOWN = 2'd1, LOW = 2'd2, UP = 2'd3;
    localparam [2:0] HOW_PRED = 3'd0, HOW_VALLEY = 3'd1, HOW_ZVS = 3'd2, HOW_RESTART = 3'd3, HOW_TIMED = 3'd4;
    localparam signed [TW-1:0] WIN = 1 << FB;
    localparam signed [CW-1:0] TRIM_MAX = (1 << (CW - 1)) - 1;
    localparam signed [CW-1:0] TRIM_MIN = -(1 << (CW - 1));

    reg [TW-1:0] t_off, t_lon, t_lo, fired_ref;
    reg [TW-1:0] pend_ref;                                           // A93: reference whose slot is awaited
    reg          pend_v;

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
    reg  [15:0] lo_n;                                               // A99: learned turn-offs (saturating)
    assign lo_timed = FIRST && cfg_lo_pred && mode_p && (lo_n >= cfg_lo_learn);
    wire signed [TW-1:0] d_lo1t = t_lon + dlo - now;                // A99: timed turn-off
    // A100: dlo's next value from the report (step 1, or adaptive) and the Ton feedforward, floored at 0
    reg  [TW-1:0] ton_q;
    reg  [7:0]    lo_step;
    reg           lo_last, lo_seen;
    wire          lo_up    = mlo_early || (mlo_err < cfg_lo_tgt);
    wire [7:0]    adm_s    = (lo_seen && (lo_up == lo_last)) ?
                             ((lo_step >= (cfg_lo_smax >> 1)) ? cfg_lo_smax : (lo_step << 1)) : 8'd1;
    wire [7:0]    step_u   = cfg_lo_adm ? adm_s : 8'd1;
    wire          ff_on    = cfg_lo_ff && (ton != ton_q);
    wire signed [TW+1:0] ton_dd = $signed({2'b00, ton}) - $signed({2'b00, ton_q});
    wire signed [TW+11:0] ff_p  = ton_dd * $signed({2'b00, cfg_lo_kff});
    wire signed [TW+11:0] fb_p  = !mlo_valid ? 0 : (lo_up ? $signed({4'd0, step_u}) : -$signed({4'd0, step_u}));
    wire signed [TW+11:0] dlo_s = $signed({12'd0, dlo}) + (ff_on ? ff_p : 0) + fb_p;
    wire [TW-1:0]         dlo_next = dlo_s[TW+11] ? {TW{1'b0}} : dlo_s[TW-1:0];
    wire [FB-1:0] f_lo1t = fine(d_lo1t, cfg_fine);
    assign arm = async_on && (state == LOW) && lo_open && !lo_timed;
    wire slot_new   = (fired_ref != ref_id);
    wire slot_miss  = cfg_slot_guard && pend_v && (pend_ref != ref_id);   // A93: the awaited slot was passed
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
            pend_ref    <= {TW{1'b0}};
            pend_v      <= 1'b0;
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
            dlo         <= {TW{1'b0}};
            lo_n        <= 16'd0;
            ton_q       <= {TW{1'b0}};
            lo_step     <= 8'd1;
            lo_last     <= 1'b0;
            lo_seen     <= 1'b0;
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
            ton_q <= ton;                                        // A100
            if (lo_timed && (mlo_valid || ff_on)) begin          // A99: sign-based correction of dlo (A100: step, FF)
                dlo <= dlo_next;
                if (mlo_valid) begin
                    lo_step <= step_u; lo_last <= lo_up; lo_seen <= 1'b1;
                end
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
                    end else if (lo_timed) begin                 // A99: timed phase-1 turn-off
                        if (due(d_lo1t)) begin
                            gl_ev <= 1'b1; gl_lvl <= 1'b0; gl_fine <= f_lo1t;
                            t_lo <= now + f_lo1t; lo_bind_cur <= 1'b0; lo_pulse <= 1'b1;
                            if (d_lo1t[TW-1]) late_fires <= late_fires + 1'b1;
                            state <= UP;
                        end else if (due(d_rs1)) begin
                            gl_ev <= 1'b1; gl_lvl <= 1'b0; gl_fine <= f_rs1;
                            t_lo <= now + f_rs1; lo_bind_cur <= 1'b0; lo_pulse <= 1'b1;
                            state <= UP;
                        end
                    end else if (async_on) begin
                        if (a_valid) begin                       // A81: edges made by the front end
                            t_lo <= a_tlo; lo_bind_cur <= 1'b1; lo_pulse <= 1'b1;
                            t_on <= a_tlo + dt_pred; on_how <= HOW_PRED; on_pulse <= 1'b1;
                            if (cfg_lo_pred) begin               // A99: learn the on-low interval
                                dlo <= a_tlo - t_lon;
                                if (lo_n != 16'hFFFF) lo_n <= lo_n + 1'b1;
                            end
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
                            if (cfg_lo_pred) begin               // A99: learn the on-low interval
                                dlo <= now - t_lon;
                                if (lo_n != 16'hFFFF) lo_n <= lo_n + 1'b1;
                            end
                            state <= UP;
                        end else if (due(d_rs1)) begin
                            gl_ev <= 1'b1; gl_lvl <= 1'b0; gl_fine <= f_rs1;
                            t_lo <= now + f_rs1; lo_bind_cur <= 1'b0; lo_pulse <= 1'b1;
                            state <= UP;
                        end
                    end else if (slot_new && (slot_miss || due(d_slot))) begin   // A93: or a missed slot
                        gl_ev <= 1'b1; gl_lvl <= 1'b0; gl_fine <= slot_miss ? {FB{1'b0}} : f_slot;
                        t_lo <= now + (slot_miss ? {FB{1'b0}} : f_slot); lo_bind_cur <= 1'b0; lo_pulse <= 1'b1;
                        fired_ref <= ref_id; pend_v <= 1'b0;
                        if (slot_miss || d_slot[TW-1]) late_fires <= late_fires + 1'b1;
                        state <= UP;
                    end else if (slot_new) begin                         // A93: waiting for this reference
                        pend_ref <= ref_id; pend_v <= 1'b1;
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
