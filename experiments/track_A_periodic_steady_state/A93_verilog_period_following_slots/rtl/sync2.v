`timescale 1ns / 1ps
// Two-flip-flop synchroniser for asynchronous comparator outputs.
// A change reaches q one to two clock edges after it happens at d.
module sync2 #(
    parameter W = 1
) (
    input  wire         clk,
    input  wire         rst,
    input  wire [W-1:0] d,
    output wire [W-1:0] q
);
    reg [W-1:0] s1, s2;

    always @(posedge clk) begin
        if (rst) begin
            s1 <= {W{1'b0}};
            s2 <= {W{1'b0}};
        end else begin
            s1 <= d;
            s2 <= s1;
        end
    end

    assign q = s2;
endmodule
