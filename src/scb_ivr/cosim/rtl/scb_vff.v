`timescale 1ns / 1ps
// A128 (extension ml_design_assist): input-voltage feed-forward on each phase's Ton. Opt-in (en); with en = 0, or
// outside mode P, ton_ph is ton for every phase, bit for bit.
// At each Vin sample (vin_valid, taken at phase 1's turn-on with Vo's), with 8 fractional bits:
// - low-passes lp2 += (vin - lp2) >> sh2, lp20 += (vin - lp20) >> sh20 (both start at the first sample);
// - the falling term g = max(lp2 - vin, 0); each phase's scale m_k = c_k g (Q24 of the Ton change, c_k signed, Q16
//   per Vin code), clamped to [-1/2, +1/4]: ton_k = ton + round(ton m_k / 2^24) (A127's learned falling-step rule);
// - phase 1's cap = k / rail, rail = (2 vin - vin_prev) - 3/4 lp20 - vo (a one-step prediction against the lag),
//   by a restoring divider started at the sample (32 clocks), so it applies from the next phase-1 turn-on;
//   rail <= 0 or k = 0: no cap (A127's cap_vin). ton_ph[0] = min(ton_0, cap).
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
    input  wire [3:0]      sh2,
    input  wire [3:0]      sh20,
    input  wire [AW-1:0]   vo_code,
    input  wire [TW-1:0]   ton,
    output wire [N*TW-1:0] ton_ph
);
    localparam LW = AW + 10;                   // signed fixed point, 8 fractional bits
    reg               init;
    reg  signed [LW-1:0] lp2, lp20;
    reg  [AW-1:0]     vprev;
    reg  signed [LW-1:0] g;
    reg  signed [31:0]   m [0:N-1];
    reg  [TW-1:0]     cap;
    reg               cap_on;

    wire signed [LW-1:0] v8    = $signed({2'b00, vin_code, 8'd0});
    wire signed [LW-1:0] lp2n  = init ? lp2 + ((v8 - lp2) >>> sh2) : v8;
    wire signed [LW-1:0] lp20n = init ? lp20 + ((v8 - lp20) >>> sh20) : v8;
    wire signed [LW-1:0] gn    = (lp2n > v8) ? lp2n - v8 : {LW{1'b0}};
    wire signed [LW+1:0] vpred = init ? $signed({v8, 1'b0}) - $signed({2'b00, vprev, 8'd0}) : v8;
    wire signed [LW+1:0] rail  = vpred - ((lp20n * 3) >>> 2) - $signed({4'b0000, vo_code, 8'd0});

    // restoring divider: q = (k << 8) / rail
    reg  [5:0]  dcnt;
    reg  [31:0] dnum, dq;
    reg  [32:0] drem;
    reg  [LW+1:0] dden;
    wire [32:0] dtry = {drem[31:0], dnum[31]} - {{(31 - LW){1'b0}}, dden};

    integer j;
    always @(posedge clk) begin
        if (rst) begin
            init <= 1'b0; lp2 <= 0; lp20 <= 0; vprev <= 0; g <= 0; cap <= 0; cap_on <= 1'b0; dcnt <= 0;
            for (j = 0; j < N; j = j + 1) m[j] <= 0;
        end else begin
            if (vin_valid) begin
                init <= 1'b1; lp2 <= lp2n; lp20 <= lp20n; vprev <= vin_code; g <= gn;
                if (rail > 0 && k != 0) begin
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
