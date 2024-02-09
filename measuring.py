import os
import subprocess


def synth_design(input_file, output_file, liberty, genus='genus', synthesized=False):

    if synthesized:
        genus_command = 'read_libs ' + liberty + '; read_hdl ' +  input_file + '; elaborate; report_area; write_hdl -mapped > ' + output_file + '_syn.v; exit;'
    else:
        genus_command = 'read_libs ' + liberty + '; read_hdl ' +  input_file + '; elaborate; synthesize -to_generic -effort high; syn_map; syn_opt; report_area; write_hdl -generic > ' + output_file + '.v; synthesize -to_generic -effort high; syn_map; syn_opt; write_hdl -mapped > ' + output_file + '_syn.v; exit;'
    area = 0
    with open(output_file+'.log', 'w') as f:
        subprocess.call([genus, '-execute', genus_command, '-log', '/dev/null'], stdout=f, stderr=subprocess.STDOUT)
    with open(output_file+'.log', 'r') as file_handle:
        line = file_handle.readline()
        while line:
            if 'Total Area' in line:
                line = file_handle.readline()
                line = file_handle.readline()
                area = line.split()[4]
                break
            line = file_handle.readline()

    os.remove(output_file+'.log')
    
    return float(area)



def get_delay(liberty, input_file, output_file, genus='genus'):

    genus_command = 'read_libs ' + liberty + '; read_hdl ' +  input_file + '; elaborate; create_clock -name clk -period 0; set_input_delay -clock clk 0 [all_inputs]; set_output_delay -clock clk 0 [all_outputs]; report_timing; exit;'
    with open(output_file, 'w') as f:
        subprocess.call([genus, '-execute', genus_command, '-log', '/dev/null'], stdout=f, stderr=subprocess.STDOUT)
    with open(output_file) as f:
        line = f.readline()
        while line:
            tokens = line.split()
            if len(tokens) >= 2 and tokens[0] == 'Slack:=':
                time = -float(tokens[1])
                break
            line = f.readline()

    return time / 1e3


def get_power(liberty, input_file, output_file, delay, genus='genus'):

    genus_command = 'read_libs ' + liberty + '; read_hdl ' +  input_file + '; elaborate; create_clock -name clk -period '+str(delay) +'; set_input_delay -clock clk 0 [all_inputs]; set_output_delay -clock clk 0 [all_outputs]; report_power; exit;'
    with open(output_file, 'w') as f:
        subprocess.call([genus, '-execute', genus_command, '-log', '/dev/null'], stdout=f, stderr=subprocess.STDOUT)
    with open(output_file) as f:
        line = f.readline()
        while line:
            tokens = line.split()
            if len(tokens) >= 6 and tokens[0] == 'Subtotal':
                power = float(tokens[4])
                break
            line = f.readline()

    return power * 1e6


liberty = ''
dir = ''

for filename in os.listdir(dir):
    if filename[:-2] == '.v':
        output_file = "./synth.v"
        area = synth_design(filename, output_file, liberty)
        delay = get_delay(liberty, output_file, './log_delay')
        power = get_power(liberty, output_file, './log_power', delay)
        os.remove(output_file)
        os.remove('./log_delay')
        os.remove('./log_power')
        print('Module: {}\tArea: {}\tDelay: {}\tPower: {}\n'.format(filename, area, delay, power))