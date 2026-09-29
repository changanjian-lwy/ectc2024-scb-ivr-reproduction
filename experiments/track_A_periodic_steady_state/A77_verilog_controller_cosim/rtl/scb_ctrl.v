`timescale 1ns / 1ps
// P24 SCB module controller in mode P: N phases on a shared time base.
//
// - The time base counts clock cycles; now = cycle << FB, in LSB units (T_clk / 2^FB).
// - The comparators are asynchronous analog outputs and enter through a 2-FF synchroniser.
// - Phase 1's turn-on time becomes t_ref. Phase k (k >= 2) turns its low side off at
//   t_ref + slot_k (D41's fixed shifts, slot_k = (k-1)*T0/N).
// - The outputs of each clock refer to the window [win_q, win_q + 2^FB): win_q is the
//   window start of the edges now on the outputs.
module scb_ctrl #(
    parameter N  = 4,
    parameter TW = 32,
    parameter FB = 5,
    parameter CW = 8
) (
    input  wire                clk,
    input  wire                rst,
    input  wire [TW-1:0]       cfg_ton,
    input  wire [TW-1:0]       cfg_rs_high,
    input  wire [TW-1:0]       cfg_rs_low,
    input  wire [TW-1:0]       cfg_dt_step,
    input  wire [TW-1:0]       cfg_dt_max,
    input  wire [(N-1)*TW-1:0] cfg_slot,       // slot offsets of phases 2..N, packed
    input  wire                cfg_pred,
    input  wire                cfg_zvs_react,
    input  wire                cfg_trim,
    input  wire                cfg_fine,
    input  wire [N*TW-1:0]     dt_init,
    input  wire [N*CW-1:0]     trim_init,
    input  wire [N-1:0]        cmp_i,          // asynchronous comparator outputs
    input  wire [N-1:0]        cmp_zl,
    input  wire [N-1:0]        cmp_zh,
    input  wire [N-1:0]        cmp_valley,
    input  wire [N-1:0]        m_valid,        // measurement pulses, clock domain
    input  wire [N-1:0]        m_early,
    input  wire [N-1:0]        m_flat,
    input  wire [N*TW-1:0]     m_tv,
    input  wire [N-1:0]        r_valid,
    input  wire [N-1:0]        r_below,
    output wire [N-1:0]        gh_ev,
    output wire [N-1:0]        gh_lvl,
    output wire [N*FB-1:0]     gh_fine,
    output wire [N-1:0]        gl_ev,
    output wire [N-1:0]        gl_lvl,
    output wire [N*FB-1:0]     gl_fine,
    output wire [2*N-1:0]      state,
    output wire [N-1:0]        on_pulse,
    output wire [2*N-1:0]      on_how,
    output wire [N-1:0]        lo_pulse,
    output wire [N-1:0]        lo_bind_cur,
    output wire [N*CW-1:0]     trim,
    output wire [N*TW-1:0]     dt_pred,
    output wire [16*N-1:0]     late_fires,
    output reg  [TW-1:0]       win_q,
    output reg  [TW-1:0]       t_ref
);
    reg  [TW-FB-1:0] cyc;
    wire [TW-1:0]    now = {cyc, {FB{1'b0}}};
    wire [N*TW-1:0]  t_on_all;

    wire [4*N-1:0] cmp_s;
    sync2 #(.W(4 * N)) u_sync (
        .clk(clk), .rst(rst),
        .d({cmp_valley, cmp_zh, cmp_zl, cmp_i}),
        .q(cmp_s)
    );

    always @(posedge clk) begin
        if (rst) begin
            cyc   <= {(TW - FB){1'b0}};
            win_q <= {TW{1'b0}};
            t_ref <= {TW{1'b0}};
        end else begin
            cyc   <= cyc + 1'b1;
            win_q <= now;
            if (on_pulse[0])
                t_ref <= t_on_all[TW-1:0];
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
                .clk(clk), .rst(rst), .now(now),
                .cfg_ton(cfg_ton), .cfg_rs_high(cfg_rs_high), .cfg_rs_low(cfg_rs_low),
                .cfg_dt_step(cfg_dt_step), .cfg_dt_max(cfg_dt_max),
                .cfg_pred(cfg_pred), .cfg_zvs_react(cfg_zvs_react), .cfg_trim(cfg_trim),
                .cfg_fine(cfg_fine),
                .dt_init(dt_init[k * TW +: TW]), .trim_init(trim_init[k * CW +: CW]),
                .slot_time(slot_t), .ref_id(t_ref),
                .c_i(cmp_s[k]), .c_zl(cmp_s[N + k]), .c_zh(cmp_s[2 * N + k]), .c_valley(cmp_s[3 * N + k]),
                .m_valid(m_valid[k]), .m_early(m_early[k]), .m_flat(m_flat[k]), .m_tv(m_tv[k * TW +: TW]),
                .r_valid(r_valid[k]), .r_below(r_below[k]),
                .gh_ev(gh_ev[k]), .gh_lvl(gh_lvl[k]), .gh_fine(gh_fine[k * FB +: FB]),
                .gl_ev(gl_ev[k]), .gl_lvl(gl_lvl[k]), .gl_fine(gl_fine[k * FB +: FB]),
                .state(state[2 * k +: 2]), .t_on(t_on_all[k * TW +: TW]),
                .on_pulse(on_pulse[k]), .on_how(on_how[2 * k +: 2]),
                .lo_pulse(lo_pulse[k]), .lo_bind_cur(lo_bind_cur[k]),
                .trim(trim[k * CW +: CW]), .dt_pred(dt_pred[k * TW +: TW]),
                .late_fires(late_fires[16 * k +: 16])
            );
        end
    endgenerate
endmodule
