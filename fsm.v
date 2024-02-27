// Description
// Generated FSM code based on excel file
module fsm (
  input clk,
  input reset_n,
  input frameStart,
  input mode,
  input frameEnd,
  input burstDone,
  output reg progress,
  output reg progress2
);
localparam STATE_SIZE = 4;

localparam   IDLE = 0,
  WAIT_FOR_START = 1,
  SINGLE_FRAME = 3,
  BURST_FRAME = 4;

reg [STATE_SIZE-1:0] state;
  always @(posedge clk or negedge reset_n) begin
    if (!reset_n)
      state <= IDLE;
    else begin
      case(state) 
        IDLE: begin
          state <= WAIT_FOR_START;
          progress <= 0;
          progress2 <= 0;
        end
        WAIT_FOR_START: begin
          if (frameStart == 1 && mode == 0) begin
            progress <= 0;
            state <= SINGLE_FRAME;
          end
          if (frameStart == 1 && mode == 1) begin
            progress <= 0;
            state <= BURST_FRAME;
          end
        end
        SINGLE_FRAME: begin
          if (frameEnd == 1) begin
            progress <= 1;
            progress2 <= 1;
            state <= WAIT_FOR_START;
          end
        end
        BURST_FRAME: begin
          if (burstDone == 1) begin
            progress <= 1;
            state <= WAIT_FOR_START;
          end
        end
      endcase
    end
  end
endmodule
