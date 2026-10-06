`timescale 1ns / 1ps
// P24 SCB module controller: N phase controllers (scb_phase), the time base, the comparator synchroniser (sync2),
// the mode register, phase slots and the output-voltage loop.
// - Mode register: reset into mode S (cfg_start_s = 1) or mode P; while hand_req is high, the next phase-1
//   high-side turn-on switches to mode P.
// - Slots: phase j's (j = 2..N) low-side turn-off is due at t_ref (phase 1's last turn-on) + cfg_slot[j - 1];
//   with cfg_slot_follow, in mode P once two phase-1 turn-ons have been seen, at t_ref + (j - 1) * T_meas / N,
//   T_meas = the last phase-1 period (P24/P25's phase shift T/nP); with cfg_slot_avg as well, once three
//   phase-1 turn-ons have been seen, at t_ref + (j - 1) * (T_meas + T_prev) / (2N), T_prev = the period before
//   (the configured slot until then). cfg_slot_guard is passed to phases 2..N.
// - Phase 1's turn-off (cfg_lo_pred): timed after cfg_lo_learn comparator-decided turn-offs (scb_phase); its crossing
//   reports mlo_* go to phase 1 only; cfg_lo_floor (A118) keeps its front end armed in timed mode, as a floor.
//   cfg_floor_late (A141) goes to every phase: a floor report after the committed turn-off moves t_on.
// - Voltage loop (mode P, cfg_vloop): at each ADC sample of Vo (taken at phase 1's turn-on), e = vref - adc_code;
//   ton_acc += ki * e (clamped) and the proportional term p_term = kp * e (A104), both with FRAC fractional bits;
//   Ton is the rounded integer part of ton_acc + p_term, clamped to [cfg_ton_min, cfg_ton_max]; otherwise
//   Ton = cfg_ton. With cfg_kp = 0 the loop is A79's integral loop.
// - Comparators (current, low/high V_DS = 0, valley) pass a 2-flip-flop synchroniser; measurement reports
//   (m_*, ml_*, r_*, a_*) arrive as one-cycle pulses.
// - C2 (multi-module): with cfg_ext_ton, Ton in mode P is ext_ton (the master's, broadcast); with the parameter
//   SLAVE = 1, phase 1 is a slotted phase like phases 2..N, its low-side turn-off at ext_slot once per reference
//   ext_ref (the master's t_ref), and it resets LOW; phase 1's front end, timed turn-off and their reports are off,
//   except C06's cfg_slave_floor: the front end armed before the slot as a floor (scb_phase cfg_slot_floor).
// - C02: with cfg_slot_lo, the period-following slots of phases 2..N are referenced to phase 1's last low-side
//   turn-off (t_lo1) instead of its high-side turn-on (t_ref), so all N low-side turn-offs are T/N apart; the
//   configured slots (mode S, or before the period is known) stay referenced to t_ref. A phase still learns of a
//   new cycle from t_ref, so its slot must lie after t_ref is seen: T/N - dt_pred > ~2 windows (a passed slot fires
//   late, counted in late_fires). t_lo1 is an output (the system's reference for slave modules).
// - A109: cfg_slot_trim gives every slotted phase (phases 2..N, and a slave's phase 1) a valley trim of its slot
//   from its residual-current reports (scb_phase); slot_ofs reports the offsets.
// - A128 (extension): with cfg_vff, in mode P each phase's Ton comes from scb_vff (Vin feed-forward); else ton_now.
//   A135: cfg_vff_rel != 0 makes phase 1's cap relative to ton (scb_vff), so it cannot bind in steady state;
//   A136: cfg_vff_rel_lp takes ton's low-pass for it; A137: cfg_vff_seed restarts scb_vff's low-passes at mode P's entry;
//   C10: cfg_vff_seed 2 seeds ton's low-pass with mode S's Ton. A148: cfg_vff_vs_kr / kt give phase 1's timed low-side
//   edge an offset from scb_vff (the volt-second law; lo_add, 0 when both are 0).
// - A132: with cfg_dep, in mode P scb_dep moves the negative-current target (dep) from phase 1's V_DS reports.
// - A133: with cfg_ph_floor, phases 2..N's front ends are armed in LOW as floors before their slots (scb_phase
//   cfg_slot_floor, C06's form); arm_n reports every phase's arm, fa_valid / fa_tlo carry phases 2..N's TDC reports.
// From A93's rtl (history: CHANGELOG.md).
module scb_ctrl #(
    parameter N    = 4,
    parameter TW   = 32,
    parameter FB   = 5,
    parameter CW   = 8,
    parameter AW   = 12,   // ADC code width
    parameter KW   = 16,   // loop gain width
    parameter KPW  = 24,   // proportional gain width (A104)
    parameter FRAC = 16,   // fractional bits of the Ton accumulator
    parameter SLAVE = 0    // C2: 1 = a slave module, its phase 1 at the external slot (ext_slot, ext_ref)
) (
    input  wire                clk,
    input  wire                rst,
    input  wire                cfg_start_s,    // 1: start in mode S (fixed timing)
    input  wire                hand_req,       // hand over to mode P at the next phase-1 turn-on
    input  wire [TW-1:0]       cfg_ton,
    input  wire [TW-1:0]       cfg_ton_min,
    input  wire [TW-1:0]       cfg_ton_max,
    input  wire [TW-1:0]       cfg_t0,
    input  wire [TW-1:0]       cfg_tdead,
    input  wire [TW-1:0]       cfg_rs_high,
    input  wire [TW-1:0]       cfg_rs_low,
    input  wire [TW-1:0]       cfg_dt_step,
    input  wire [TW-1:0]       cfg_dt_max,
    input  wire [(N-1)*TW-1:0] cfg_slot,
    input  wire                cfg_pred,
    input  wire                cfg_zvs_react,
    input  wire                cfg_trim,
    input  wire                cfg_fine,
    input  wire                cfg_vloop,
    input  wire [AW-1:0]       cfg_vref_code,
    input  wire [KW-1:0]       cfg_ki,
    input  wire [KPW-1:0]      cfg_kp,         // A104: proportional gain
    input  wire                cfg_ext_ton,    // C2: in mode P, Ton = ext_ton (the master's, broadcast)
    input  wire [TW-1:0]       ext_ton,        // C2
    input  wire [TW-1:0]       ext_slot,       // C2 (SLAVE): phase 1's low-side turn-off slot
    input  wire [TW-1:0]       ext_ref,        // C2 (SLAVE): the reference that slot belongs to (the master's t_ref)
    input  wire [N*TW-1:0]     dt_init,
    input  wire [N*CW-1:0]     trim_init,
    input  wire [N-1:0]        cmp_i,
    input  wire [N-1:0]        cmp_zl,
    input  wire [N-1:0]        cmp_zh,
    input  wire [N-1:0]        cmp_valley,
    input  wire [N-1:0]        m_valid,
    input  wire [N-1:0]        m_early,
    input  wire [N-1:0]        m_flat,
    input  wire [N*TW-1:0]     m_tv,
    input  wire [N-1:0]        r_valid,
    input  wire [N-1:0]        r_below,
    input  wire                adc_valid,
    input  wire [AW-1:0]       adc_code,
    input  wire                cfg_async,
    input  wire                a_valid,
    input  wire [TW-1:0]       a_tlo,
    input  wire [N-1:0]        fa_valid,       // A133: phases 2..N's front-end reports (bit k: phase k + 1)
    input  wire [N*TW-1:0]     fa_tlo,
    input  wire                cfg_low_pred,   // A89
    input  wire [N*TW-1:0]     dtl_init,       // A89
    input  wire [TW-1:0]       cfg_dtl_step,   // A89
    input  wire [TW-1:0]       cfg_dtl_max,    // A89
    input  wire [N-1:0]        ml_valid,       // A89
    input  wire [N-1:0]        ml_early,       // A89
    input  wire [N*TW-1:0]     ml_tv,          // A89
    output wire [N*TW-1:0]     dtl,            // A89
    input  wire [TW-1:0]       cfg_blank,      // A89: current-comparator blanking, LSB
    input  wire                cfg_err_low,    // A92
    input  wire                cfg_err_high,   // A92
    input  wire [TW-1:0]       cfg_el_tgt,     // A92
    input  wire [TW-1:0]       cfg_eh_tgt,     // A92
    input  wire [3:0]          cfg_err_shift,  // A92
    input  wire [N*TW-1:0]     ml_err,         // A92
    input  wire [N*TW-1:0]     m_err,          // A92
    input  wire                cfg_slot_follow,// A93
    input  wire                cfg_slot_guard, // A93
    input  wire                cfg_slot_avg,   // A97
    input  wire                cfg_slot_lo,    // C02: following slots from phase 1's low-side turn-off
    input  wire                cfg_slot_trim,  // A109: valley trim of the slotted phases' turn-offs
    input  wire [7:0]          cfg_st_smax,    // A109: its largest step, LSB
    input  wire                cfg_lo_pred,    // A99: timed phase-1 turn-off after learning
    input  wire [15:0]         cfg_lo_learn,   // A99
    input  wire [TW-1:0]       cfg_lo_tgt,     // A99
    input  wire                mlo_valid,      // A99: phase 1's crossing report at its timed turn-off
    input  wire                mlo_early,      // A99
    input  wire [TW-1:0]       mlo_err,        // A99
    input  wire                cfg_lo_adm,     // A100: adaptive dlo step
    input  wire [7:0]          cfg_lo_smax,    // A100
    input  wire                cfg_lo_ff,      // A100: Ton feedforward to dlo
    input  wire [7:0]          cfg_lo_kff,     // A100
    input  wire                cfg_lo_floor,   // A118: phase 1's front end as a floor in timed mode
    input  wire                cfg_slave_floor,// C06 (SLAVE): phase 1's front end as a floor before its slot
    input  wire                cfg_ph_floor,   // A133: phases 2..N's front ends as floors before their slots
    input  wire                cfg_floor_late, // A141: a late floor report moves t_on (scb_phase)
    input  wire                cfg_vff,        // A128: Vin feed-forward on each phase's Ton (scb_vff), mode P
    input  wire                vin_valid,      // A128: Vin ADC sample (with Vo's)
    input  wire [AW-1:0]       vin_code,       // A128
    input  wire [N*12-1:0]     cfg_vff_c,      // A128: falling-step coefficients, Q16 per Vin code
    input  wire [23:0]         cfg_vff_k,      // A128: phase-1 cap constant, LSB x Vin code
    input  wire [9:0]          cfg_vff_rel,    // A135: relative phase-1 cap, 1 + mu in Q8 (0: the absolute cap, k)
    input  wire                cfg_vff_rel_lp, // A136: the relative cap on ton's low-pass
    input  wire [1:0]          cfg_vff_seed,   // A137: restart the feed-forward's low-passes at mode P's entry (C10: 2)
    input  wire [3:0]          cfg_vff_sh2,    // A128
    input  wire [3:0]          cfg_vff_sh20,   // A128
    input  wire [AW-1:0]       cfg_vff_gth,    // A129: falling-term gate, Vin codes (0: always on)
    input  wire [AW-1:0]       cfg_vff_vo,     // A128: Vo in Vin codes
    input  wire signed [15:0]  cfg_vff_vs_kr,  // A148: phase 1's low-side edge offset, rail coefficient (scb_vff)
    input  wire signed [15:0]  cfg_vff_vs_kt,  // A148: its Ton coefficient (0 and 0: no offset)
    input  wire                cfg_dep,        // A132: slow loop on the negative-current target (scb_dep), mode P
    input  wire [3:0]          cfg_dep_wsh,    // A132: window of 2^wsh phase-1 reports
    input  wire [7:0]          cfg_dep_smax,   // A132: largest step, codes
    input  wire [7:0]          cfg_dep_min,    // A132: dep range, codes (signed)
    input  wire [7:0]          cfg_dep_max,    // A132
    input  wire [AW-1:0]       cfg_dep_ehold,  // A132: |vref - Vo code| above which a window is spoiled
    input  wire                v_valid,        // A132: phase 1's V_DS comparator report at its predictive turn-on
    input  wire                v_high,         // A132: V_DS > V_set at the edge
    output wire [7:0]          dep,            // A132: depth code, signed: the target is i_target - dep x trim LSB
    output wire [TW-1:0]       dlo1,           // A99: phase 1's dlo
    output wire                lo_timed1,      // A99: phase 1's turn-off is timed
    output wire [TW-1:0]       t_lo1,          // C02: phase 1's last low-side turn-off
    output wire [N*TW-1:0]     slot_ofs,       // A109: each phase's slot valley-trim offset, LSB (signed)
    output wire                arm1,
    output wire [N-1:0]        arm_n,          // A133: every phase's front end armed
    output wire [N-1:0]        gh_ev,
    output wire [N-1:0]        gh_lvl,
    output wire [N*FB-1:0]     gh_fine,
    output wire [N-1:0]        gl_ev,
    output wire [N-1:0]        gl_lvl,
    output wire [N*FB-1:0]     gl_fine,
    output wire [2*N-1:0]      state,
    output wire [N-1:0]        on_pulse,
    output wire [3*N-1:0]      on_how,
    output wire [N-1:0]        lo_pulse,
    output wire [N-1:0]        lo_bind_cur,
    output wire [N*CW-1:0]     trim,
    output wire [N*TW-1:0]     dt_pred,
    output wire [16*N-1:0]     late_fires,
    output reg  [TW-1:0]       win_q,
    output reg  [TW-1:0]       t_ref,
    output reg                 mode_p,
    output wire [TW-1:0]       ton_now
);
    reg  [TW-FB-1:0] cyc;
    wire [TW-1:0]    now = {cyc, {FB{1'b0}}};
    wire [N*TW-1:0]  t_on_all;
    wire [N-1:0]     arm_all;
    assign arm1 = arm_all[0];
    assign arm_n = arm_all;

    // ---- voltage loop ----
    localparam AW1 = TW + FRAC;
    reg  signed [AW1-1:0] ton_acc;
    wire signed [AW:0]    err  = $signed({1'b0, cfg_vref_code}) - $signed({1'b0, adc_code});
    wire signed [AW+KW+1:0] step = err * $signed({1'b0, cfg_ki});
    wire signed [AW1-1:0] acc_next = ton_acc + {{(AW1 - AW - KW - 2){step[AW+KW+1]}}, step};
    wire signed [AW1-1:0] acc_min  = $signed({cfg_ton_min, {FRAC{1'b0}}});
    wire signed [AW1-1:0] acc_max  = $signed({cfg_ton_max, {FRAC{1'b0}}});
    reg  signed [AW1-1:0] p_term;                                  // A104
    wire signed [AW+KPW+1:0] pstep = err * $signed({1'b0, cfg_kp});
    wire signed [AW1-1:0] ton_sum  = ton_acc + p_term;
    wire signed [AW1-1:0] ton_cl   = (ton_sum < acc_min) ? acc_min : (ton_sum > acc_max) ? acc_max : ton_sum;
    wire signed [AW1-1:0] acc_rnd  = ton_cl + (1 <<< (FRAC - 1));
    wire [TW-1:0] ton_loop = acc_rnd[AW1-1:FRAC];
    assign ton_now = (cfg_vloop && mode_p) ? ton_loop : (cfg_ext_ton && mode_p) ? ext_ton : cfg_ton;   // C2

    wire [N*TW-1:0] ton_ph;                    // A128: each phase's Ton (ton_now unless cfg_vff in mode P)
    wire signed [TW-1:0] lo_add;               // A148: phase 1's low-side edge offset
    scb_vff #(.N(N), .TW(TW), .AW(AW)) u_vff (
        .clk(clk), .rst(rst), .en(cfg_vff && mode_p), .vin_valid(vin_valid), .vin_code(vin_code), .c(cfg_vff_c),
        .k(cfg_vff_k), .rel(cfg_vff_rel), .rel_lp(cfg_vff_rel_lp), .seed(cfg_vff_seed), .sh2(cfg_vff_sh2), .sh20(cfg_vff_sh20), .gth(cfg_vff_gth), .vo_code(cfg_vff_vo), .ton(ton_now),
        .vs_kr(cfg_vff_vs_kr), .vs_kt(cfg_vff_vs_kt), .ton_ph(ton_ph), .lo_add(lo_add)
    );

    scb_dep #(.AW(AW), .DW(8)) u_dep (                                // A132
        .clk(clk), .rst(rst), .en(cfg_dep && mode_p), .v_valid(v_valid), .v_high(v_high), .adc_valid(adc_valid),
        .err(err), .wsh(cfg_dep_wsh), .smax(cfg_dep_smax), .dmin(cfg_dep_min), .dmax(cfg_dep_max), .ehold(cfg_dep_ehold),
        .dep(dep)
    );

    wire [4*N-1:0] cmp_s;
    sync2 #(.W(4 * N)) u_sync (
        .clk(clk), .rst(rst),
        .d({cmp_valley, cmp_zh, cmp_zl, cmp_i}),
        .q(cmp_s)
    );

    reg [TW-1:0] t_per;                        // A93: last phase-1 period, LSB
    reg [1:0]    n_ref;                        // A93: phase-1 turn-ons seen (saturates at 2)
    wire         per_ok = cfg_slot_follow && mode_p && (n_ref == 2'd2);
    reg [TW-1:0] t_per2;                       // A97: the period before t_per, LSB
    reg          per3;                         // A97: three phase-1 turn-ons seen (t_per2 valid)
    wire         use_follow = cfg_slot_avg ? (per_ok && per3) : per_ok;

    always @(posedge clk) begin
        if (rst) begin
            t_per   <= {TW{1'b0}};
            n_ref   <= 2'd0;
            t_per2  <= {TW{1'b0}};
            per3    <= 1'b0;
        end else if (on_pulse[0]) begin
            t_per   <= t_on_all[TW-1:0] - t_ref;
            if (n_ref != 2'd2) n_ref <= n_ref + 1'b1;
            t_per2  <= t_per;
            if (n_ref == 2'd2) per3 <= 1'b1;
        end
    end

    always @(posedge clk) begin
        if (rst) begin
            cyc     <= {(TW - FB){1'b0}};
            win_q   <= {TW{1'b0}};
            t_ref   <= {TW{1'b0}};
            mode_p  <= !cfg_start_s;
            ton_acc <= $signed({cfg_ton, {FRAC{1'b0}}});
            p_term  <= {AW1{1'b0}};
        end else begin
            cyc   <= cyc + 1'b1;
            win_q <= now;
            if (on_pulse[0]) begin
                t_ref <= t_on_all[TW-1:0];
                if (!mode_p && hand_req)
                    mode_p <= 1'b1;
            end
            if (adc_valid && cfg_vloop && mode_p) begin
                ton_acc <= (acc_next < acc_min) ? acc_min : (acc_next > acc_max) ? acc_max : acc_next;
                p_term  <= {{(AW1 - AW - KPW - 2){pstep[AW+KPW+1]}}, pstep};
            end
        end
    end

    wire [N*TW-1:0] dlo_all;                   // A99
    wire [N-1:0]    lo_timed_all;
    assign dlo1 = dlo_all[TW-1:0];
    assign lo_timed1 = lo_timed_all[0];
    wire [N*TW-1:0] t_lo_all;                  // C02
    assign t_lo1 = t_lo_all[TW-1:0];

    genvar k;
    generate
        for (k = 0; k < N; k = k + 1) begin : g_ph
            wire [TW-1:0] slot_t;
            wire [TW-1:0] ref_k = (k == 0 && SLAVE) ? ext_ref : t_ref;             // C2
            if (k == 0) begin : g_first
                assign slot_t = SLAVE ? ext_slot : {TW{1'b0}};                         // C2
            end else begin : g_rest
                wire [TW-1:0] slot_follow = cfg_slot_avg ? (k * (t_per + t_per2)) / (2 * N)  // A97: k * T_avg / N
                                                         : (k * t_per) / N;                  // A93: k * T / N
                assign slot_t = ((use_follow && cfg_slot_lo) ? t_lo1 : t_ref)                // C02
                                + (use_follow ? slot_follow : cfg_slot[(k - 1) * TW +: TW]);
            end
            localparam IS_FIRST = (k == 0 && !SLAVE) ? 1 : 0;                         // C2
            scb_phase #(.TW(TW), .FB(FB), .CW(CW), .FIRST(IS_FIRST)) u_ph (
                .clk(clk), .rst(rst), .now(now), .mode_p(mode_p), .ton(ton_ph[k * TW +: TW]),
                .cfg_t0(cfg_t0), .cfg_tdead(cfg_tdead),
                .cfg_rs_high(cfg_rs_high), .cfg_rs_low(cfg_rs_low),
                .cfg_dt_step(cfg_dt_step), .cfg_dt_max(cfg_dt_max),
                .cfg_pred(cfg_pred), .cfg_zvs_react(cfg_zvs_react), .cfg_trim(cfg_trim),
                .cfg_fine(cfg_fine),
                .dt_init(dt_init[k * TW +: TW]), .trim_init(trim_init[k * CW +: CW]),
                .slot_time(slot_t), .ref_id(ref_k),
                .c_i(cmp_s[k]), .c_zl(cmp_s[N + k]), .c_zh(cmp_s[2 * N + k]), .c_valley(cmp_s[3 * N + k]),
                .m_valid(m_valid[k]), .m_early(m_early[k]), .m_flat(m_flat[k]), .m_tv(m_tv[k * TW +: TW]),
                .r_valid(r_valid[k]), .r_below(r_below[k]),
                .cfg_async(IS_FIRST ? cfg_async : 1'b0), .a_valid((IS_FIRST || (k == 0 && SLAVE)) ? a_valid : (k > 0 && cfg_ph_floor) ? fa_valid[k] : 1'b0),
                .a_tlo((k > 0 && cfg_ph_floor) ? fa_tlo[k * TW +: TW] : a_tlo),                  // A133
                .arm(arm_all[k]),
                .gh_ev(gh_ev[k]), .gh_lvl(gh_lvl[k]), .gh_fine(gh_fine[k * FB +: FB]),
                .gl_ev(gl_ev[k]), .gl_lvl(gl_lvl[k]), .gl_fine(gl_fine[k * FB +: FB]),
                .state(state[2 * k +: 2]), .t_on(t_on_all[k * TW +: TW]),
                .on_pulse(on_pulse[k]), .on_how(on_how[3 * k +: 3]),
                .lo_pulse(lo_pulse[k]), .lo_bind_cur(lo_bind_cur[k]),
                .trim(trim[k * CW +: CW]), .dt_pred(dt_pred[k * TW +: TW]),
                .late_fires(late_fires[16 * k +: 16]),
                .cfg_low_pred(cfg_low_pred), .dtl_init(dtl_init[k * TW +: TW]),                 // A89
                .cfg_dtl_step(cfg_dtl_step), .cfg_dtl_max(cfg_dtl_max),
                .ml_valid(ml_valid[k]), .ml_early(ml_early[k]), .ml_tv(ml_tv[k * TW +: TW]),
                .dtl(dtl[k * TW +: TW]), .cfg_blank(cfg_blank),
                .cfg_err_low(cfg_err_low), .cfg_err_high(cfg_err_high),                         // A92
                .cfg_el_tgt(cfg_el_tgt), .cfg_eh_tgt(cfg_eh_tgt), .cfg_err_shift(cfg_err_shift),
                .ml_err(ml_err[k * TW +: TW]), .m_err(m_err[k * TW +: TW]),
                .cfg_slot_guard(IS_FIRST ? 1'b0 : cfg_slot_guard),                            // A93
                .cfg_lo_pred(IS_FIRST ? cfg_lo_pred : 1'b0), .cfg_lo_learn(cfg_lo_learn),      // A99
                .cfg_lo_tgt(cfg_lo_tgt), .mlo_valid(IS_FIRST ? mlo_valid : 1'b0), .mlo_early(mlo_early),
                .mlo_err(mlo_err), .dlo(dlo_all[k * TW +: TW]), .lo_timed(lo_timed_all[k]),
                .cfg_lo_adm(cfg_lo_adm), .cfg_lo_smax(cfg_lo_smax), .cfg_lo_ff(cfg_lo_ff), .cfg_lo_kff(cfg_lo_kff),  // A100
                .t_lo_q(t_lo_all[k * TW +: TW]),                                                // C02
                .cfg_slot_trim(cfg_slot_trim), .cfg_st_smax(cfg_st_smax),                       // A109
                .cfg_lo_floor(IS_FIRST ? cfg_lo_floor : 1'b0),                                  // A118
                .cfg_slot_floor((k == 0 && SLAVE) ? cfg_slave_floor : (k > 0) ? cfg_ph_floor : 1'b0),   // C06; A133
                .cfg_floor_late(cfg_floor_late),                                                // A141
                .lo_add(IS_FIRST ? lo_add : {TW{1'b0}}),                                        // A148
                .sofs(slot_ofs[k * TW +: TW])
            );
        end
    endgenerate
endmodule
