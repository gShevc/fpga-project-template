`timescale 1ns / 1ps

module top_tb;

    logic       clk;
    logic       rst_n;
//    logic [3:0] led;

    top dut (
        .clk   (clk),
        .rst_n (rst_n)    );

    initial clk = 1'b0;
    always #5 clk = ~clk;

    initial begin
        $dumpfile("top_tb.vcd");
        $dumpvars(0, top_tb);

        rst_n = 1'b0;
        repeat (10) @(posedge clk);
        rst_n = 1'b1;

        repeat (200) @(posedge clk);
        $finish;
    end

endmodule
