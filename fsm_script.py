import pandas as pd
import argparse
import os
import random
import numpy as np
import time
import secrets
import re

def generate_logical_expression(inputs, conditions):
    # Construct the logical expression
    logical_expression = "("
    for input_signal, condition in zip(inputs, conditions):
        logical_expression += f"{input_signal} == {condition} && "
    logical_expression = logical_expression.rstrip(" && ")  # Remove the trailing "and"
    logical_expression += ")"
    return logical_expression

def generate_output_assignments(outputs, values):
    # Construct the output assignments
    assignments = []
    for output_signal, value in zip(outputs, values):
        assignments.append(f"{output_signal} <= {value};")
    return assignments

def split_field(field):
    # Find all occurrences of words separated by commas
    matches = re.findall(r'\b\w+\b', field)

    # Iterate over each match
    for match in matches:
        return [value.strip() for value in field.split(',')]

def generate_fsm_verilog(excel_file):
    fsm_code = ""
    fsm_code += "// Description\n"
    fsm_code += "// Generated FSM code based on excel file\n"
    fsm_code += "module fsm (\n"
    fsm_code += "  input clk,\n"
    fsm_code += "  input reset_n,\n"
    
    fsm_transition = pd.read_excel(excel_file)
    # Read the Excel file
    ports_df = pd.read_excel(excel_file, sheet_name='Ports')
    
    for index, row in ports_df.iterrows():
        inputs = row['INPUTS']
        input_description = row['INPUT DESCRIPTION']
        input_width = row['INPUT WIDTH']
        if pd.notnull(inputs):
            if pd.notnull(input_width) and input_width < 2 :
                fsm_code += f"  input {inputs},\n"
            else:
                fsm_code += f"  input [{int(input_width)-1}:0] {inputs},\n"

    for index, row in ports_df.iterrows():
        outputs = row['OUTPUTS']
        output_description = row['OUTPUT DESCRIPTION']
        output_width = row['OUTPUT WIDTH']
        if pd.notnull(outputs):
            if pd.notnull(output_width) and output_width < 2:
                fsm_code += f"  output reg {outputs},\n"
            else:
                fsm_code += f"  output reg [{int(output_width)-1}:0] {outputs},\n"

    # Remove the trailing comma from the last port declaration
    fsm_code = fsm_code.rstrip(",\n") + "\n);\n"

    # Filter out empty or NaN state names
    states_df = fsm_transition.dropna(subset=['STATE NAME'])
    
    # Calculate the number of states
    num_states = len(states_df)

    # Define Verilog parameters for state size and state names
    fsm_code += "localparam STATE_SIZE = {};\n\n".format(num_states)
    fsm_code += "localparam "
    for index, row in states_df.iterrows():
        fsm_code += f"  {row['STATE NAME'].upper().replace(' ', '_')} = {index},\n"
    fsm_code = fsm_code.rstrip(",\n") + ";\n\n"

    # Define Verilog state registers
    fsm_code += "reg [STATE_SIZE-1:0] state;\n"

    # Define FSM transition logic
    fsm_code += "  always @(posedge clk or negedge reset_n) begin\n"
    fsm_code += "    if (!reset_n)\n"
    fsm_code += "      state <= IDLE;\n"
    fsm_code += "    else begin\n"
    #fsm_code += "  end\n\n"

    #fsm_code += "  always @(*) begin\n"
    fsm_code += "      case(state) \n"

    for i, row in fsm_transition.iterrows():
        state = row['STATE NAME']
        next_state = row['NEXT STATE']
        input_signals = (str(row['INPUT']))
        input_conditions = (str(row['CONDITION']))
        output_signals = (str(row['OUTPUT']))
        output_values = (str(row['VALUE']))
        # Example usage within FSM code generation
        input_signals_str = str(row['INPUT'])
        input_conditions_str = str(row['CONDITION'])
        output_signals_str = str(row['OUTPUT'])
        output_values_str = str(row['VALUE'])
        # Split the strings into lists
        input_signals = input_signals_str.split(',') if ',' in input_signals_str else [input_signals_str]
        input_conditions = input_conditions_str.split(',') if ',' in input_conditions_str else [input_conditions_str]
        output_signals = output_signals_str.split(',') if ',' in output_signals_str else [output_signals_str]
        output_values = output_values_str.split(',') if ',' in output_values_str else [output_values_str]
        # Remove leading and trailing whitespaces from each element
        input_signals = [signal.strip() for signal in input_signals]
        input_conditions = [condition.strip() for condition in input_conditions]
        output_signals = [signal.strip() for signal in output_signals]
        output_values = [signal.strip() for signal in output_values]
        current_row = row
        # Check if there is a next row
        if i +1 < len(fsm_transition):
            next_row = fsm_transition.iloc[i + 1]
        else:
            next_row = None
        if not(pd.isna(state)):
            fsm_code += f"        {state}: begin\n"
            if input_signals == ['clk']:
                fsm_code += f"          state <= {next_state};\n"
                fsm_code += f"          " + "\n          ".join(generate_output_assignments(output_signals, output_values)) + "\n"
            else:
                fsm_code += f"          if {generate_logical_expression(input_signals, input_conditions)} begin\n"
                fsm_code += f"            " + "\n            ".join(generate_output_assignments(output_signals, output_values)) + "\n"
                fsm_code += f"            state <= {next_state};\n"
                fsm_code += f"          end\n"
            if not(next_row is None):
                if not(pd.isna(next_row['STATE NAME'])):
                    fsm_code += f"        end\n" 
            else:
                fsm_code += f"        end\n"
        else:
            fsm_code += f"          if {generate_logical_expression(input_signals, input_conditions)} begin\n"
            fsm_code += f"            " + "\n            ".join(generate_output_assignments(output_signals, output_values)) + "\n"
            fsm_code += f"            state <= {next_state};\n"
            fsm_code += f"          end\n"
            if not(next_row is None):
                if not(pd.isna(next_row['STATE NAME'])):
                    fsm_code += f"        end\n" 
            else:
                fsm_code += f"        end\n"
        
    # End the case block and always block
    fsm_code += "      endcase\n"
    fsm_code += "    end\n"
    fsm_code += "  end\n"
        
    fsm_code += "endmodule"
    return fsm_code


if __name__ == "__main__":
    # Create an ArgumentParser object
    parser = argparse.ArgumentParser(description='Generate testbench from Excel file.')

    # Add an argument for the Excel file name
    parser.add_argument('excel_file', type=str, help='Excel file containing register map')

    # Parse the command-line arguments
    args = parser.parse_args()

    # Check if the provided file exists
    if not os.path.exists(args.excel_file):
        print(f"Error: File '{args.excel_file}' not found.")
        exit()

    # Generate the testbench using the provided Excel file
    fsm_code = generate_fsm_verilog(args.excel_file)

    # Print the generated testbench code
    print(fsm_code)