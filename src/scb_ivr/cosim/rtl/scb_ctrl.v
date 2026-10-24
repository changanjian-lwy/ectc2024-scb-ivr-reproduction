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
//   Ton = cfg_ton. With cfg_kp = 0 the loop is A79's integral loop. A224: with cfg_kd, a derivative term
//   d_term = -kd * (adc_code - the previous sample) is added while |the change| >= cfg_kd_db codes (else 0), held to
//   the next sample like p_term; cfg_kd = 0: none. A227: with cfg_kd_hold, d_term is 0 at a sample whose PI output
//   (ton_acc + p_term after the sample) is at or below the lower Ton limit (the light-load / skipping regime);
//   A229: or within cfg_kd_band Ton LSB above it (a skipping burst's PI output sits there).
// - Comparators (current, low/high V_DS = 0, valley) pass a 2-flip-flop synchroniser; measurement reports
//   (m_*, ml_*, r_*, a_*) arrive as one-cycle pulses. A236: m_pos with each valley report (the current at the
//   low-side turn-off had not reversed); with cfg_early_hold an early report with it leaves that phase's dt_pred.
//   A241: cfg_dt_fall goes to every phase (a report lowers dt_pred by at most that much; 0: no limit). A242: with
//   cfg_late_hold a late valley report with m_pos also leaves that phase's dt_pred. A244: both holds act only from
//   cfg_hold_wait phase-1 turn-ons after mode P's entry (0: at once), so the handover keeps the learner as before.
// - A245 (ladder balance): with cfg_bal, each phase's rail report at its low-side turn-off (b_valid; b_hi / b_lo: the
//   rail above Vin / 4 + band or below Vin / 4 - band) moves the Ton trims of phases 2..N by cfg_bal_step / 16 LSB:
//   a phase's own report up when high, down when low, phase 1's report every other phase the other way. The trims
//   (output bal, LSB) are clamped to +-cfg_bal_max LSB and held at 0 outside mode P; without cfg_bal Ton is as before.
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
//   C10: cfg_vff_seed 2 seeds ton's low-pass with mode S's Ton. A223: cfg_vff_rgth limits the relative cap to samples
//   where Vin rises (scb_vff). A148: cfg_vff_vs_kr / kt give phase 1's timed low-side edge an offset from scb_vff (the
//   volt-second law; lo_add, 0 when both are 0).
// - A184: mode S runs at cfg_ton_s; the loop's reset value (ton_acc) and scb_vff's C10 seed keep cfg_ton, so a short
//   mode-S period can have its own trim. cfg_ton_s = cfg_ton is the old controller bit for bit.
// - A215: with cfg_ton_lat = M != 0 the phases read their Ton (and phase 1's lo_add) from registers, loaded M clocks
//   after the last change of anything the Ton arithmetic reads (the loop's sample, scb_vff's updates, the handover,
//   a slave's ext_ton), so that arithmetic is a multi-cycle path of M clocks and nothing else in the path between a
//   phase's registers; a new Ton reaches the phases M + 1 clocks later than with cfg_ton_lat = 0, where they read
//   the arithmetic directly (the old controller bit for bit).
// - A216: with cfg_skip, in mode P a round is skipped while the loop's Ton is at its lower limit and the last Vo
//   sample is above vref + cfg_skip_hi (+ cfg_skip_lo once skipping): skip_q, latched at phase 1's low-side turn-on,
//   withholds phase 1's next turn-on (scb_phase hold; skip1 tells the front end to make none either). The skipped
//   turn-on counts as a reference for the slots (t_ref, the period), so phases 2..N turn their low sides off at
//   their slots and stay off too (idle). Phase 1 then ticks every period (smp: the ADC samples) and, at the first
//   tick where the condition no longer holds, turns its low side on; phases 2..N follow at that instant plus their
//   slots, and the next cycle is a normal one from the valley. The period measured across a pause is not taken.
// - A220: with cfg_zcd (and cfg_async) the pause's last low-side intervals end at zero current: phase 1's while
//   skip_q is high, phase k's when its high side turned off with skip_q high (zpend); the front ends report the
//   turn-offs (fa_valid / fa_tlo for phases 2..N, as A133's), and a slotted phase is held from then on. Such a
//   pause leaves the slots' period as it was (A221): its skipped instant, from a zero-current turn-off, is early.
// - A132: with cfg_dep, in mode P scb_dep moves the negative-current target (dep) from phase 1's V_DS reports.
// - A133: with cfg_ph_floor, phases 2..N's front ends are armed in LOW as floors before their slots (scb_phase
//   cfg_slot_floor, C06's form); arm_n reports every phase's arm, fa_valid / fa_tlo carry phases 2..N's TDC reports.
// - A238: with cfg_sink, in mode P a Vo sample above vref + cfg_sink_hi with the loop's Ton at its lower limit sets
//   sink, and it stays set until a sample at or below vref + cfg_sink_lo; while it is set no round is skipped (a
//   paused module resumes at its next tick) and the front ends use the sink target instead of i_target (the bridge),
//   so that at the lower Ton limit each phase's mean current turns negative and the module sinks.
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
    input  wire [TW-1:0]       cfg_ton_s,      // A184: mode S's Ton (cfg_ton stays the loop's reset value and scb_vff's seed)
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
    input  wire [KPW-1:0]      cfg_kd,         // A224: derivative gain on the Vo sample's change (0: none)
    input  wire [3:0]          cfg_kd_db,      // A224: ... only while |the change| >= this many ADC codes
    input  wire                cfg_kd_hold,    // A227: ... and not while the PI output is at the lower Ton limit
    input  wire                cfg_early_hold, // A236: an early valley report with m_pos leaves dt_pred
    input  wire [TW-1:0]       cfg_dt_fall,    // A241: a valley report lowers dt_pred by at most this (0: no limit)
    input  wire                cfg_late_hold,  // A242: a late valley report with m_pos leaves dt_pred
    input  wire [7:0]          cfg_hold_wait,  // A244: the holds act from this many phase-1 turn-ons in mode P
    input  wire                cfg_bal,        // A245: ladder balance on phases 2..N's Ton
    input  wire [7:0]          cfg_bal_step,   // A245: ... this many 1/16 LSB per report outside the band
    input  wire [TW-1:0]       cfg_bal_max,    // A245: ... trims clamped to +-this many LSB
    input  wire [TW-1:0]       cfg_kd_band,    // A229: ... or within this many Ton LSB above it (0: at the limit)
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
    input  wire [N-1:0]        m_pos,          // A236: the current at the low-side turn-off had not reversed
    input  wire [N-1:0]        b_valid,        // A245: a rail report at the phase's low-side turn-off
    input  wire [N-1:0]        b_hi,           // A245: ... its rail above Vin / 4 + band
    input  wire [N-1:0]        b_lo,           // A245: ... below Vin / 4 - band
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
    input  wire [AW-1:0]       cfg_vff_rgth,   // A223: the relative cap only while Vin rises by >= this many codes (0: always)
    input  wire [3:0]          cfg_vff_sh2,    // A128
    input  wire [3:0]          cfg_vff_sh20,   // A128
    input  wire [AW-1:0]       cfg_vff_gth,    // A129: falling-term gate, Vin codes (0: always on)
    input  wire [AW-1:0]       cfg_vff_vo,     // A128: Vo in Vin codes
    input  wire signed [15:0]  cfg_vff_vs_kr,  // A148: phase 1's low-side edge offset, rail coefficient (scb_vff)
    input  wire signed [15:0]  cfg_vff_vs_kt,  // A148: its Ton coefficient (0 and 0: no offset)
    input  wire [5:0]          cfg_ton_lat,    // A215: clocks the Ton arithmetic gets before the phases' registers load (0: none)
    input  wire                cfg_skip,       // A216: skip rounds at the lower Ton limit while Vo is high (mode P)
    input  wire [AW-1:0]       cfg_skip_hi,    // A216: start above vref + this, ADC codes
    input  wire [AW-1:0]       cfg_skip_lo,    // A216: continue above vref + this
    output wire                skip1,          // A216: phase 1's next turn-on is skipped (the front end makes none)
    output wire                smp,            // A216: a tick of the paused module: the ADC samples (one cycle)
    output wire                idle,           // A216: the module is paused
    output wire                res1,           // A217: phase 1 is in its resume interval (the front end's threshold moves)
    input  wire                cfg_sink,       // A238: sink mode at the lower Ton limit while Vo is high (mode P)
    input  wire [AW-1:0]       cfg_sink_hi,    // A238: start above vref + this, ADC codes
    input  wire [AW-1:0]       cfg_sink_lo,    // A238: continue above vref + this
    output wire                sink,           // A238: the front ends use the sink target
    input  wire                cfg_zcd,        // A220: the pause's last low-side intervals end at zero current
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
    output wire [N*TW-1:0]     bal,            // A245: each phase's Ton trim, LSB (signed)
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
    wire signed [AW1-1:0] acc_cl   = (acc_next < acc_min) ? acc_min : (acc_next > acc_max) ? acc_max : acc_next;
    wire signed [AW1-1:0] pi_next  = acc_cl + {{(AW1 - AW - KPW - 2){pstep[AW+KPW+1]}}, pstep};   // A227
    wire signed [AW1-1:0] acc_hold = acc_min + $signed({cfg_kd_band, {FRAC{1'b0}}});   // A229
    wire                  d_hold   = cfg_kd_hold && (pi_next <= acc_hold);
    reg  signed [AW1-1:0] d_term;                                  // A224
    wire signed [AW1-1:0] ton_sum  = ton_acc + p_term + d_term;
    wire signed [AW1-1:0] ton_cl   = (ton_sum < acc_min) ? acc_min : (ton_sum > acc_max) ? acc_max : ton_sum;
    wire signed [AW1-1:0] acc_rnd  = ton_cl + (1 <<< (FRAC - 1));
    wire [TW-1:0] ton_loop = acc_rnd[AW1-1:FRAC];
    assign ton_now = (cfg_vloop && mode_p) ? ton_loop : (cfg_ext_ton && mode_p) ? ext_ton : cfg_ton_s; // C2, A184
    wire [TW-1:0] ton_seed = (cfg_vloop && mode_p) ? ton_loop : (cfg_ext_ton && mode_p) ? ext_ton : cfg_ton;  // A184

    // ---- A216: skipped rounds ----
    reg  [AW-1:0]   vo_q;                      // the last Vo sample
    wire signed [AW:0]       dcode = $signed({1'b0, adc_code}) - $signed({1'b0, vo_q});          // A224
    wire [AW:0]              dmag  = dcode[AW] ? -dcode : dcode;
    wire signed [AW+KPW+1:0] dstep = -dcode * $signed({1'b0, cfg_kd});
    reg             skip_q, mod_idle, per_hold;
    reg  [TW-1:0]   res_t;                     // the last resume's instant (phase 1's low-side turn-on)
    wire [N-1:0]    sk_p, tk_p, res_p;
    wire [N*TW-1:0] t_lon_all;
    wire [N-1:0]    res_all;                   // A217
    assign res1 = res_all[0];
    reg  [N-1:0]    zpend;                     // A220: phase k's last pulse before a pause has ended
    integer         zk;
    // the three comparisons change with a sample only; with cfg_ton_lat they are read from registers loaded with the
    // phases' Ton (A215), so no path of the Ton arithmetic reaches a phase within a clock
    wire            fl_c = (ton_sum <= acc_min);                                       // Ton at its lower limit
    wire            hi_c = ({1'b0, vo_q} > {1'b0, cfg_vref_code} + {1'b0, cfg_skip_hi});
    wire            lo_c = ({1'b0, vo_q} > {1'b0, cfg_vref_code} + {1'b0, cfg_skip_lo});
    reg             fl_r, hi_r, lo_r;
    wire            lat_sk = (cfg_ton_lat != 6'd0);
    reg             sink_q;                    // A238
    wire            skip_c = cfg_skip && cfg_vloop && mode_p && (lat_sk ? fl_r : fl_c) && !sink_q
                             && ((skip_q || mod_idle) ? (lat_sk ? lo_r : lo_c) : (lat_sk ? hi_r : hi_c));
    wire            snk_hi = ({1'b0, adc_code} > {1'b0, cfg_vref_code} + {1'b0, cfg_sink_hi});   // A238: this sample
    wire            snk_lo = ({1'b0, adc_code} > {1'b0, cfg_vref_code} + {1'b0, cfg_sink_lo});
    assign sink  = sink_q;
    assign skip1 = skip_q;
    assign smp   = tk_p[0];
    assign idle  = mod_idle;

    wire [N*TW-1:0] ton_ph_c;                  // A128: each phase's Ton (ton_now unless cfg_vff in mode P)
    wire signed [TW-1:0] lo_add_c;             // A148: phase 1's low-side edge offset
    wire            vff_upd;                   // A215
    scb_vff #(.N(N), .TW(TW), .AW(AW)) u_vff (
        .clk(clk), .rst(rst), .en(cfg_vff && mode_p), .vin_valid(vin_valid), .vin_code(vin_code), .c(cfg_vff_c),
        .k(cfg_vff_k), .rel(cfg_vff_rel), .rel_lp(cfg_vff_rel_lp), .seed(cfg_vff_seed), .rgth(cfg_vff_rgth), .sh2(cfg_vff_sh2), .sh20(cfg_vff_sh20), .gth(cfg_vff_gth), .vo_code(cfg_vff_vo), .ton(ton_now), .tseed(ton_seed),
        .vs_kr(cfg_vff_vs_kr), .vs_kt(cfg_vff_vs_kt), .ton_ph(ton_ph_c), .lo_add(lo_add_c), .upd(vff_upd)
    );

    // A215: the phases' registers of the Ton path. lat_ev is high in the clock before an edge that changes one of
    // the arithmetic's sources (a slave's ext_ton: in the clock after its change); the load comes cfg_ton_lat clocks
    // after the last such edge. In reset the registers follow the arithmetic, and load once more in the first clock.
    reg  [N*TW-1:0] ton_ph_r;
    reg  signed [TW-1:0] lo_add_r;
    reg  [5:0]      lat_cnt;
    reg  [TW-1:0]   ext_q;
    wire            lat_on = (cfg_ton_lat != 6'd0);
    wire            lat_ev = (adc_valid && cfg_vloop && mode_p) || vff_upd || (on_pulse[0] && !mode_p && hand_req)
                             || (cfg_ext_ton && (ext_ton != ext_q));
    wire [N*TW-1:0] ton_ph = lat_on ? ton_ph_r : ton_ph_c;
    wire signed [TW-1:0] lo_add = lat_on ? lo_add_r : lo_add_c;
    always @(posedge clk) begin
        ext_q <= ext_ton;
        if (rst) begin
            ton_ph_r <= ton_ph_c; lo_add_r <= lo_add_c; lat_cnt <= 6'd1;
            fl_r <= 1'b0; hi_r <= 1'b0; lo_r <= 1'b0;                 // A216
        end else if (lat_ev) begin
            lat_cnt <= cfg_ton_lat;
        end else if (lat_cnt != 6'd0) begin
            lat_cnt <= lat_cnt - 1'b1;
            if (lat_cnt == 6'd1) begin
                ton_ph_r <= ton_ph_c; lo_add_r <= lo_add_c;
                fl_r <= fl_c; hi_r <= hi_c; lo_r <= lo_c;             // A216
            end
        end
    end

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

    reg  [7:0]   hold_n;                       // A244: phase-1 turn-ons in mode P (saturates at cfg_hold_wait)
    wire         hold_ok = (hold_n >= cfg_hold_wait);
    always @(posedge clk) begin
        if (rst || !mode_p)
            hold_n <= 8'd0;
        else if (on_pulse[0] && !hold_ok)
            hold_n <= hold_n + 1'b1;
    end

    wire [TW-1:0] t_von = t_lo1 + dt_pred[TW-1:0];                    // A216: a skipped turn-on's instant
    always @(posedge clk) begin
        if (rst) begin
            t_per   <= {TW{1'b0}};
            n_ref   <= 2'd0;
            t_per2  <= {TW{1'b0}};
            per3    <= 1'b0;
        end else if ((on_pulse[0] && !per_hold) || (sk_p[0] && !cfg_zcd)) begin   // A216; A221: zcd keeps it
            t_per   <= (sk_p[0] ? t_von : t_on_all[TW-1:0]) - t_ref;
            if (n_ref != 2'd2) n_ref <= n_ref + 1'b1;
            t_per2  <= t_per;
            if (n_ref == 2'd2) per3 <= 1'b1;
        end
    end

    always @(posedge clk) begin                                       // A216
        if (rst) begin
            vo_q <= cfg_vref_code; skip_q <= 1'b0; mod_idle <= 1'b0; per_hold <= 1'b0; res_t <= {TW{1'b0}};
            zpend <= {N{1'b0}}; sink_q <= 1'b0;
        end else begin
            for (zk = 1; zk < N; zk = zk + 1)                         // A220: at phase k's high-side turn-off
                if (gh_ev[zk] && !gh_lvl[zk]) zpend[zk] <= cfg_zcd && cfg_async && mode_p && skip_q;
            if (res_p[0]) zpend <= {N{1'b0}};
            if (adc_valid) vo_q <= adc_code;
            if (adc_valid)                                            // A238: the previous sample's Ton limit
                sink_q <= cfg_sink && cfg_vloop && mode_p && (sink_q ? snk_lo : (snk_hi && (lat_sk ? fl_r : fl_c)));
            if (gl_ev[0] && gl_lvl[0]) skip_q <= skip_c;              // at phase 1's low-side turn-on
            if (on_pulse[0]) per_hold <= 1'b0;
            if (sk_p[0]) begin mod_idle <= 1'b1; per_hold <= 1'b1; end
            if (res_p[0]) begin mod_idle <= 1'b0; res_t <= t_lon_all[TW-1:0]; end
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
            d_term  <= {AW1{1'b0}};
        end else begin
            cyc   <= cyc + 1'b1;
            win_q <= now;
            if (on_pulse[0]) begin
                t_ref <= t_on_all[TW-1:0];
                if (!mode_p && hand_req)
                    mode_p <= 1'b1;
            end else if (sk_p[0]) begin                              // A216: the skipped turn-on is the slots' reference
                t_ref <= t_von;
            end
            if (adc_valid && cfg_vloop && mode_p) begin
                ton_acc <= acc_cl;
                p_term  <= {{(AW1 - AW - KPW - 2){pstep[AW+KPW+1]}}, pstep};
                d_term  <= (dmag >= {{(AW - 3){1'b0}}, cfg_kd_db} && !d_hold) ? {{(AW1 - AW - KPW - 2){dstep[AW+KPW+1]}}, dstep}
                                                                            : {AW1{1'b0}};   // A224, A227
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
            wire [TW-1:0] res_tk;                                                      // A216
            wire [TW-1:0] ref_k = (k == 0 && SLAVE) ? ext_ref : t_ref;             // C2
            if (k == 0) begin : g_first
                assign slot_t = SLAVE ? ext_slot : {TW{1'b0}};                         // C2
                assign res_tk = {TW{1'b0}};
            end else begin : g_rest
                wire [TW-1:0] slot_follow = cfg_slot_avg ? (k * (t_per + t_per2)) / (2 * N)  // A97: k * T_avg / N
                                                         : (k * t_per) / N;                  // A93: k * T / N
                assign slot_t = ((use_follow && cfg_slot_lo) ? t_lo1 : t_ref)                // C02
                                + (use_follow ? slot_follow : cfg_slot[(k - 1) * TW +: TW]);
                assign res_tk = res_t + (use_follow ? slot_follow : cfg_slot[(k - 1) * TW +: TW]);   // A216
            end
            wire [TW-1:0] ton_k;                                                       // A245
            if (k == 0) begin : g_bal0
                assign ton_k = ton_ph[TW-1:0];
                assign bal[TW-1:0] = {TW{1'b0}};
            end else begin : g_bal
                reg  signed [TW+5:0] bal_q;                                            // 1/16 LSB
                wire signed [TW+5:0] st = $signed({{(TW-2){1'b0}}, cfg_bal_step});
                wire signed [TW+5:0] mx = $signed({2'b00, cfg_bal_max, 4'b0000});
                wire signed [TW+5:0] dk = (b_valid[k] && b_hi[k]) ? st : (b_valid[k] && b_lo[k]) ? -st : 0;
                wire signed [TW+5:0] d1 = (b_valid[0] && b_hi[0]) ? -st : (b_valid[0] && b_lo[0]) ? st : 0;
                wire signed [TW+5:0] nx = bal_q + dk + d1;
                always @(posedge clk) begin
                    if (rst || !mode_p || !cfg_bal)
                        bal_q <= 0;
                    else
                        bal_q <= (nx > mx) ? mx : (nx < -mx) ? -mx : nx;
                end
                wire signed [TW+5:0] bal_l = bal_q >>> 4;
                wire signed [TW+5:0] sum = $signed({6'b000000, ton_ph[k * TW +: TW]}) + bal_l;
                assign ton_k = !cfg_bal ? ton_ph[k * TW +: TW] : (sum < 1) ? {{(TW-1){1'b0}}, 1'b1} : sum[TW-1:0];
                assign bal[k * TW +: TW] = bal_l[TW-1:0];
            end
            localparam IS_FIRST = (k == 0 && !SLAVE) ? 1 : 0;                         // C2
            scb_phase #(.TW(TW), .FB(FB), .CW(CW), .FIRST(IS_FIRST)) u_ph (
                .clk(clk), .rst(rst), .now(now), .mode_p(mode_p), .ton(ton_k),
                .cfg_t0(cfg_t0), .cfg_tdead(cfg_tdead),
                .cfg_rs_high(cfg_rs_high), .cfg_rs_low(cfg_rs_low),
                .cfg_dt_step(cfg_dt_step), .cfg_dt_max(cfg_dt_max),
                .cfg_pred(cfg_pred), .cfg_zvs_react(cfg_zvs_react), .cfg_trim(cfg_trim),
                .cfg_fine(cfg_fine),
                .dt_init(dt_init[k * TW +: TW]), .trim_init(trim_init[k * CW +: CW]),
                .slot_time(slot_t), .ref_id(ref_k),
                .c_i(cmp_s[k]), .c_zl(cmp_s[N + k]), .c_zh(cmp_s[2 * N + k]), .c_valley(cmp_s[3 * N + k]),
                .m_valid(m_valid[k]), .m_early(m_early[k]), .m_flat(m_flat[k]), .m_tv(m_tv[k * TW +: TW]),
                .m_pos(m_pos[k]), .cfg_early_hold(cfg_early_hold && hold_ok),                   // A236, A244
                .cfg_dt_fall(cfg_dt_fall), .cfg_late_hold(cfg_late_hold && hold_ok),             // A241, A242, A244
                .r_valid(r_valid[k]), .r_below(r_below[k]),
                .cfg_async(IS_FIRST ? cfg_async : 1'b0), .a_valid((IS_FIRST || (k == 0 && SLAVE)) ? a_valid : (k > 0 && (cfg_ph_floor || cfg_zcd)) ? fa_valid[k] : 1'b0),
                .a_tlo((k > 0 && (cfg_ph_floor || cfg_zcd)) ? fa_tlo[k * TW +: TW] : a_tlo),      // A133, A220
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
                .lo_add(IS_FIRST ? lo_add : $signed({TW{1'b0}})),                               // A148
                .hold(IS_FIRST ? skip_q : (k > 0) ? (mod_idle || zpend[k]) : 1'b0),             // A216, A220
                .zcd(IS_FIRST ? (cfg_zcd && cfg_async && skip_q) : (k > 0) ? zpend[k] : 1'b0),   // A220
                .tk_skip(skip_c), .tk_per((n_ref == 2'd2) ? t_per : cfg_t0), .res_time(res_tk),
                .sk_pulse(sk_p[k]), .tk_pulse(tk_p[k]), .res_pulse(res_p[k]), .t_lon_q(t_lon_all[k * TW +: TW]), .res_lo(res_all[k]),
                .sofs(slot_ofs[k * TW +: TW])
            );
        end
    endgenerate
endmodule
