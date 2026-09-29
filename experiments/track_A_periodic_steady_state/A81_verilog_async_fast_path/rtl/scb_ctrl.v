`timescale 1ns / 1ps
// P24 SCB module controller: start-up in mode S, handover, mode P switching, and the output-voltage loop.
//
// A81 version of A80's scb_ctrl (A80's copy is unchanged): cfg_async, arm1, a_valid, a_tlo for phase 1's
// asynchronous front-end path (see scb_phase.v).
//
// A80 version of A77's scb_ctrl (A77's copy is unchanged). Additions:
//   - mode register: reset into mode S (cfg_start_s = 1) or mode P. When hand_req is high, the
//     next phase-1 high-side turn-on switches to mode P (the A71/A73 handover rule).
//   - voltage loop (A79's rule, mode P only): at each ADC sample of Vo (taken by the analog side at
//     phase 1's turn-on), ton_acc += ki * (vref_code - adc_code). ton_acc has FRAC fractional bits,
//     and the Ton used by the phases is its rounded integer part (in LSB), clamped to
//     [cfg_ton_min, cfg_ton_max].
// Time base, synchroniser and slots as in A77.
module scb_ctrl #(
    parameter N    = 4,
    parameter TW   = 32,
    parameter FB   = 5,
    parameter CW   = 8,
    parameter AW   = 12,   // ADC code width
    parameter KW   = 16,   // loop gain width
    parameter FRAC = 16    // fractional bits of the Ton accumulator
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
    output wire                arm1,
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

    // ---- voltage loop ----
    localparam AW1 = TW + FRAC;
    reg  signed [AW1-1:0] ton_acc;
    wire signed [AW:0]    err  = $signed({1'b0, cfg_vref_code}) - $signed({1'b0, adc_code});
    wire signed [AW+KW+1:0] step = err * $signed({1'b0, cfg_ki});
    wire signed [AW1-1:0] acc_next = ton_acc + {{(AW1 - AW - KW - 2){step[AW+KW+1]}}, step};
    wire signed [AW1-1:0] acc_min  = $signed({cfg_ton_min, {FRAC{1'b0}}});
    wire signed [AW1-1:0] acc_max  = $signed({cfg_ton_max, {FRAC{1'b0}}});
    wire signed [AW1-1:0] acc_rnd  = ton_acc + (1 <<< (FRAC - 1));
    wire [TW-1:0] ton_loop = acc_rnd[AW1-1:FRAC];
    assign ton_now = (cfg_vloop && mode_p) ? ton_loop : cfg_ton;

    wire [4*N-1:0] cmp_s;
    sync2 #(.W(4 * N)) u_sync (
        .clk(clk), .rst(rst),
        .d({cmp_valley, cmp_zh, cmp_zl, cmp_i}),
        .q(cmp_s)
    );

    always @(posedge clk) begin
        if (rst) begin
            cyc     <= {(TW - FB){1'b0}};
            win_q   <= {TW{1'b0}};
            t_ref   <= {TW{1'b0}};
            mode_p  <= !cfg_start_s;
            ton_acc <= $signed({cfg_ton, {FRAC{1'b0}}});
        end else begin
            cyc   <= cyc + 1'b1;
            win_q <= now;
            if (on_pulse[0]) begin
                t_ref <= t_on_all[TW-1:0];
                if (!mode_p && hand_req)
                    mode_p <= 1'b1;
            end
            if (adc_valid && cfg_vloop && mode_p)
                ton_acc <= (acc_next < acc_min) ? acc_min : (acc_next > acc_max) ? acc_max : acc_next;
        end
    end

    genvar k;
    generate
        for (k = 0; k < N; k = k + 1) begin : g_ph
            wire [TW-1:0] slot_t;
            if (k == 0) begin : g_first
                assign slot_t = {TW{1'b0}};
            end else begin : g_rest
                assign slot_t = t_ref + cfg_slot[(k - 1) * TW +: TW];
            end
            scb_phase #(.TW(TW), .FB(FB), .CW(CW), .FIRST(k == 0 ? 1 : 0)) u_ph (
                .clk(clk), .rst(rst), .now(now), .mode_p(mode_p), .ton(ton_now),
                .cfg_t0(cfg_t0), .cfg_tdead(cfg_tdead),
                .cfg_rs_high(cfg_rs_high), .cfg_rs_low(cfg_rs_low),
                .cfg_dt_step(cfg_dt_step), .cfg_dt_max(cfg_dt_max),
                .cfg_pred(cfg_pred), .cfg_zvs_react(cfg_zvs_react), .cfg_trim(cfg_trim),
                .cfg_fine(cfg_fine),
                .dt_init(dt_init[k * TW +: TW]), .trim_init(trim_init[k * CW +: CW]),
                .slot_time(slot_t), .ref_id(t_ref),
                .c_i(cmp_s[k]), .c_zl(cmp_s[N + k]), .c_zh(cmp_s[2 * N + k]), .c_valley(cmp_s[3 * N + k]),
                .m_valid(m_valid[k]), .m_early(m_early[k]), .m_flat(m_flat[k]), .m_tv(m_tv[k * TW +: TW]),
                .r_valid(r_valid[k]), .r_below(r_below[k]),
                .cfg_async(k == 0 ? cfg_async : 1'b0), .a_valid(k == 0 ? a_valid : 1'b0), .a_tlo(a_tlo),
                .arm(arm_all[k]),
                .gh_ev(gh_ev[k]), .gh_lvl(gh_lvl[k]), .gh_fine(gh_fine[k * FB +: FB]),
                .gl_ev(gl_ev[k]), .gl_lvl(gl_lvl[k]), .gl_fine(gl_fine[k * FB +: FB]),
                .state(state[2 * k +: 2]), .t_on(t_on_all[k * TW +: TW]),
                .on_pulse(on_pulse[k]), .on_how(on_how[3 * k +: 3]),
                .lo_pulse(lo_pulse[k]), .lo_bind_cur(lo_bind_cur[k]),
                .trim(trim[k * CW +: CW]), .dt_pred(dt_pred[k * TW +: TW]),
                .late_fires(late_fires[16 * k +: 16])
            );
        end
    endgenerate
endmodule
