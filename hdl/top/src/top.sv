// top.sv -- LED blinker example
// Toggles LEDs in a rotating pattern at ~1 Hz given a 100 MHz input clock.

`timescale 1ns / 1ps

module top (
    input  logic       clk,
    input  logic       rst_n);

    localparam int CLK_FREQ = 100_000_000;
    localparam int HALF_SEC = CLK_FREQ / 2;

    logic [31:0] counter;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            counter <= '0;
  //          led     <= 4'b0001;
        end else begin
            if (counter == HALF_SEC - 1) begin
                counter <= '0;
  //              led     <= {led[2:0], led[3]};
            end else begin
                counter <= counter + 1;
            end
        end
    end

endmodule
