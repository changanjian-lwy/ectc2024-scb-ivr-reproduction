`timescale 1ns / 1ps
// A128 (extension ml_design_assist): input-voltage feed-forward on each phase's Ton. Opt-in (en); with en = 0, or
// outside mode P, ton_ph is ton for every phase, bit for bit.
// At each Vin sample (vin_valid, taken at phase 1's turn-on with Vo's), with 8 fractional bits:
// - low-passes lp2 += (vin - lp2) >> sh2, lp20 += (vin - lp20) >> sh20 (both start at the first sample);
// - the falling term g = max(lp2 - vin, 0); each phase's scale m_k = c_k g (Q24 of the Ton change, c_k signed, Q16
//   per Vin code), clamped to [-1/2, +1/4]: ton_k = ton + round(ton m_k / 2^24) (A127's learned falling-step rule);
// - the falling term is gated by Vin's fall rate (A129): it acts from the sample where g >= gth codes until g is back to
//   0; gth = 0 keeps it always on;
// - phase 1's cap = k / rail, rail = (2 vin - vin_prev) - 3/4 lp20 - vo (a one-step prediction against the lag),
//   by a restoring divider started at the sample (32 clocks), so it applies from the next phase-1 turn-on;
//   rail <= 0 or k = 0: no cap (A127's cap_vin). ton_ph[0] = min(ton_0, cap).
// - A135: with rel != 0 the cap is relative instead: cap = ton x ((rss x rel) >> 8) / rail, rss = lp20 - 3/4 lp20 - vo
//   (the rail with Vin at its low-pass), rel = 1 + mu in Q8; in steady state rail = rss, so the cap is (1 + mu) ton and
//   never binds, whatever L or the load. k is then unused. rss <= 0: no cap.
// - A136: with rel_lp the relative cap uses ton's low-pass tlp += (ton - tlp) >> sh20 (Q8, updated at each sample, as
//   lp20) instead of ton, so a loop that raises ton during a transient does not raise the cap with it.
module scb_vff #(
    parameter N  = 4,
    parameter TW = 32,
    parameter AW = 12
) (
    input  wire            clk,
    input  wire            rst,
    input  wire            en,
    input  wire            vin_valid,
    input  wire [AW-1:0]   vin_code,
    input  wire [N*12-1:0] c,
    input  wire [23:0]     k,
    input  wire [9:0]      rel,
    input  wire            rel_lp,
    input  wire [3:0]      sh2,
    input  wire [3:0]      sh20,
    input  wire [AW-1:0]   gth,
    input  wire [AW-1:0]   vo_code,
    input  wire [TW-1:0]   ton,
    output wire [N*TW-1:0] ton_ph
);
    localparam LW = AW + 10;                   // signed fixed point, 8 fractional bits
    reg               init;
    reg  signed [LW-1:0] lp2, lp20;
    reg  [AW-1:0]     vprev;
    reg  signed [LW-1:0] g;
    reg               gate;
    reg  signed [31:0]   m [0:N-1];
    reg  [TW-1:0]     cap;
    reg               cap_on;
    reg  signed [TW+9:0] tlp;                  // A136: ton's low-pass, Q8

    wire signed [LW-1:0] v8    = $signed({2'b00, vin_code, 8'd0});
    wire signed [LW-1:0] lp2n  = init ? lp2 + ((v8 - lp2) >>> sh2) : v8;
    wire signed [LW-1:0] lp20n = init ? lp20 + ((v8 - lp20) >>> sh20) : v8;
    wire signed [LW-1:0] gn    = (lp2n > v8) ? lp2n - v8 : {LW{1'b0}};
    wire                 gaten = (gn >= $signed({2'b00, gth, 8'd0})) ? 1'b1 : ((gn == 0) ? 1'b0 : gate);
    wire signed [LW+1:0] vpred = init ? $signed({v8, 1'b0}) - $signed({2'b00, vprev, 8'd0}) : v8;
    wire signed [LW+1:0] rail  = vpred - ((lp20n * 3) >>> 2) - $signed({4'b0000, vo_code, 8'd0});
    wire signed [LW+1:0] rss   = $signed({{2{lp20n[LW-1]}}, lp20n}) - ((lp20n * 3) >>> 2) - $signed({4'b0000, vo_code, 8'd0});
    wire signed [LW+12:0] rssk = (rss * $signed({1'b0, rel})) >>> 8;            // A135: Q8
    wire signed [TW+9:0] ton8  = $signed({2'b00, ton, 8'd0});                    // A136
    wire signed [TW+9:0] tlpn  = init ? tlp + ((ton8 - tlp) >>> sh20) : ton8;
    wire [TW-1:0]        tnum  = rel_lp ? tlpn[TW+7:8] : ton;
    wire [TW+LW+12:0]    rnum = tnum * rssk[LW+11:0];
    wire [31:0]          rnum32 = (|rnum[TW+LW+12:32]) ? 32'hFFFFFFFF : rnum[31:0];

    // restoring divider: q = (k << 8) / rail, or with rel (A135) q = ton x rssk / rail
    reg  [5:0]  dcnt;
    reg  [31:0] dnum, dq;
    reg  [32:0] drem;
    reg  [LW+1:0] dden;
    wire [32:0] dtry = {drem[31:0], dnum[31]} - {{(31 - LW){1'b0}}, dden};

    integer j;
    always @(posedge clk) begin
        if (rst) begin
            init <= 1'b0; lp2 <= 0; lp20 <= 0; tlp <= 0; vprev <= 0; g <= 0; gate <= 1'b0; cap <= 0; cap_on <= 1'b0; dcnt <= 0;
            for (j = 0; j < N; j = j + 1) m[j] <= 0;
        end else begin
            if (vin_valid) begin
                init <= 1'b1; lp2 <= lp2n; lp20 <= lp20n; tlp <= tlpn; vprev <= vin_code; gate <= gaten; g <= gaten ? gn : {LW{1'b0}};
                if (rail > 0 && rel != 0 && rss > 0) begin                      // A135
                    dnum <= rnum32; dden <= rail; drem <= 0; dq <= 0; dcnt <= 6'd32;
                end else if (rail > 0 && rel == 0 && k != 0) begin
                    dnum <= {k, 8'd0}; dden <= rail; drem <= 0; dq <= 0; dcnt <= 6'd32;
                end else begin
                    cap_on <= 1'b0; dcnt <= 0;
                end
            end else if (dcnt != 0) begin
                if (!dtry[32]) begin drem <= dtry; dq <= {dq[30:0], 1'b1}; end
                else begin drem <= {drem[31:0], dnum[31]}; dq <= {dq[30:0], 1'b0}; end
                dnum <= {dnum[30:0], 1'b0};
                dcnt <= dcnt - 1'b1;
                if (dcnt == 6'd1) begin
                    cap <= (dtry[32] ? {dq[30:0], 1'b0} : {dq[30:0], 1'b1});
                    cap_on <= 1'b1;
                end
            end
            for (j = 0; j < N; j = j + 1) begin
                if ($signed(c[j * 12 +: 12]) * g > 32'sd4194304) m[j] <= 32'sd4194304;          // +1/4
                else if ($signed(c[j * 12 +: 12]) * g < -32'sd8388608) m[j] <= -32'sd8388608;   // -1/2
                else m[j] <= $signed(c[j * 12 +: 12]) * g;
            end
        end
    end

    genvar q;
    generate
        for (q = 0; q < N; q = q + 1) begin : g_ph
            wire signed [TW+33:0] prod = $signed({2'b00, ton}) * m[q];
            wire [TW-1:0] tk = ton + ((prod + 34'sd8388608) >>> 24);
            wire [TW-1:0] tc = (q == 0 && cap_on && cap < tk) ? cap : tk;
            assign ton_ph[q * TW +: TW] = en ? tc : ton;
        end
    endgenerate
endmodule
