`timescale 1ns / 1ps
// A132: slow loop on the negative-current target (the depth). Opt-in (en); with en = 0 from reset dep stays 0 and the
// bridge's target is i_target, bit for bit; en falling (e.g. leaving mode P) holds dep and restarts the window.
// Each phase-1 predictive turn-on brings one report (v_valid) of a V_DS comparator at the edge, v_high = V_DS > V_set;
// the Vo ADC sample of the same edge (adc_valid, err = vref - code) spoils its window when |err| > ehold codes (a
// transient is not a depth error). A window is W = 2^wsh reports. At the end of a clean window: up = (2 highs > W)
// (a tie is shallower); the step doubles while consecutive decisions agree, up to smax, and returns to 1 when they
// differ or after a spoiled window (A100's lo_adm, Dong 2022's variable step); dep += up ? step : -step, clamped to
// [dmin, dmax]. dep > 0 is deeper: the bridge's target is i_target - dep * trim_lsb_a.
module scb_dep #(
    parameter AW = 12,
    parameter DW = 8
) (
    input  wire                 clk,
    input  wire                 rst,
    input  wire                 en,
    input  wire                 v_valid,
    input  wire                 v_high,
    input  wire                 adc_valid,
    input  wire signed [AW:0]   err,
    input  wire [3:0]           wsh,
    input  wire [DW-1:0]        smax,
    input  wire [DW-1:0]        dmin,       // signed
    input  wire [DW-1:0]        dmax,       // signed
    input  wire [AW-1:0]        ehold,
    output reg  signed [DW-1:0] dep
);
    reg  [15:0]   cnt, highs;
    reg           spoil, have_last, last_up;
    reg  [DW-1:0] step;

    wire [AW:0]   aerr   = err[AW] ? -err : err;
    wire          bad    = adc_valid && (aerr > {1'b0, ehold});
    wire [15:0]   cnt1   = cnt + 16'd1;
    wire [15:0]   highs1 = highs + {15'd0, v_high};
    wire          full   = v_valid && (cnt1 == (16'd1 << wsh));
    wire          up     = {highs1, 1'b0} > (17'd1 << wsh);
    wire          agree  = have_last && (up == last_up);
    wire [DW:0]   step2  = {step, 1'b0};
    wire [DW-1:0] step_n = !agree ? {{(DW - 1){1'b0}}, 1'b1} : (step2 > {1'b0, smax}) ? smax : step2[DW-1:0];
    wire signed [DW+1:0] sum = up ? dep + $signed({2'b00, step_n}) : dep - $signed({2'b00, step_n});
    wire signed [DW+1:0] lo  = $signed(dmin);
    wire signed [DW+1:0] hi  = $signed(dmax);
    wire signed [DW+1:0] cl  = (sum < lo) ? lo : (sum > hi) ? hi : sum;

    always @(posedge clk) begin
        if (rst) begin
            dep <= {DW{1'b0}};
            cnt <= 16'd0; highs <= 16'd0; spoil <= 1'b0; have_last <= 1'b0; last_up <= 1'b0; step <= {{(DW - 1){1'b0}}, 1'b1};
        end else if (!en) begin
            cnt <= 16'd0; highs <= 16'd0; spoil <= 1'b0; have_last <= 1'b0;
        end else begin
            if (full) begin
                cnt <= 16'd0; highs <= 16'd0; spoil <= 1'b0;
                if (spoil || bad) begin
                    have_last <= 1'b0;
                end else begin
                    dep <= cl[DW-1:0]; step <= step_n; last_up <= up; have_last <= 1'b1;
                end
            end else begin
                if (v_valid) begin
                    cnt <= cnt1; highs <= highs1;
                end
                if (bad)
                    spoil <= 1'b1;
            end
        end
    end
endmodule
