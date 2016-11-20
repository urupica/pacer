#!/usr/bin/env python3

import datetime, os, subprocess, sys, json
from fractions import Fraction

'''
Usage: $ splittimes.py input.txt hh:mm [nopdf]

'''

def main():
    file_name = sys.argv[1]
    hh, mm = map(int,sys.argv[2].split(':'))
    print_to_stdout = True
    create_pdf = False if len(sys.argv) > 3 and sys.argv[3] == 'nopdf' else True
    calculate_split_times(file_name, hh, mm, print_to_stdout, create_pdf)


def compute_between_distances(dist1, dist2):
    return False

def compute_between_indices(distances, partial_distances, height_differences, paces_per_section, partial_times, locations, i, j):
    data = (
            #str(i+1).rjust(2),
            float(distances[i+1])/1000,
            float(partial_distances[i])/1000,
            float(height_differences[i]*100)/partial_distances[i],
            str(datetime.timedelta(seconds = int(paces_per_section[i]*1000)))[3:7],
            str(datetime.timedelta(seconds = int(paces_per_section[i]*partial_distances[i])))[:7],
            str(datetime.timedelta(seconds = partial_times[i]))[:7],
            locations[i+1])
    #if pront_to_stdout == True:# and i+1 in markant_sections:
    return data



def calculate_split_times(file_name, hours, minutes, stdout, pdf):
    name = None
    output_name = None
    points = 0
    distances = []
    heights = []
    #display = []
    locations = []
    locations_abbr = []
    markant_distances = []
    markant_names = []
    markant_abbr = []
    markant_sections = []
    alpha = Fraction(2,2)

    with open(file_name) as input_data:
        json_data = json.loads(input_data.read())
        name = json_data['name']
        #name = input_data.readline().strip()[6:]
        output_name = json_data['output']
        #output_name = input_data.readline().strip()[8:]
        #for (i,line) in enumerate(input_data):
        for (i, point) in enumerate(json_data['points']):
            points += 1
            #parts = line.rstrip().split(';')
            #distances.append(int(1000*float(parts[0])))
            distances.append(int(1000*point['dist']))
            #heights.append(int(parts[1]))
            heights.append(point['alt'])
            #display.append(True if parts[2] == 'yes' else False)
            #if parts[2] == 'yes':
            if point['primary']:
                markant_sections.append(i)
                #markant_distances.append(1000*float(parts[0]))
                markant_distances.append(1000*float(point['dist']))
                #markant_names.append(parts[4])
                markant_names.append(point['full name'])
                #markant_abbr.append(parts[3])
                markant_abbr.append(point['short name'])
            #locations_abbr.append(parts[3])
            locations_abbr.append(point['short name'])
            #locations.append(parts[4])
            locations.append(point['full name'])

    total_time = (hours*60 + minutes)*60

    tex_file_name = '{}_{}_{}'.format(output_name, hours, minutes)
    all_data = []
    
    #split times for the sections
    partial_distances = [distances[i]-distances[i-1] for i in range(1,points)]
    height_differences = [heights[i]-heights[i-1] for i in range(1,points)]
    total_distance = distances[-1]
    global_pace = Fraction(total_time, total_distance)
    global_slope = Fraction(heights[-1] - heights[0], total_distance)
    paces_per_section = []
    for i in range(points - 1):
        local_slope = Fraction(height_differences[i], partial_distances[i])
        paces_per_section.append(global_pace*(1 + alpha*(local_slope - global_slope)))
    partial_times = []
    partial = 0
    for i in range(len(partial_distances)):
        partial += paces_per_section[i]*partial_distances[i]
        partial_times.append(int(partial))



    data_1 = [[0,0,'-','-','0:00:00', '0:00:00',locations[0]]]
    for i in range(points - 1):
        data_1.append(compute_between_indices(distances, partial_distances, height_differences, paces_per_section, partial_times, locations, i, i+1))
    all_data.append(data_1)
    
    partial_times = [0]
    partial_time = 0
    section = 0
    distance_used = 0
    height_start = heights[0]
    #average_gradients = []
    partial_distance = 0
    while partial_distance <= distances[-1]-1000:
        section_begin = section
        distance_used_begin = distance_used
        section_distance = 0
        while section < len(partial_distances) and partial_distances[section] - distance_used <= 1000 - section_distance:
            partial_time += paces_per_section[section]*(partial_distances[section] - distance_used)
            section_distance += (partial_distances[section] - distance_used)
            distance_used = 0
            section += 1
        if section_distance < 1000:
            partial_time += paces_per_section[section]*(1000 - section_distance)
            distance_used += (1000 - section_distance)
        partial_times.append(int(partial_time))
    
        if section == len(partial_distances):
            section -= 1
        height_end = heights[section] + (float(distance_used) / partial_distances[section]) * height_differences[section]
        height_start = heights[section_begin] + (float(distance_used_begin) / partial_distances[section_begin]) * height_differences[section_begin]
    
        #average_gradients.append(100*float(height_end-height_start)/1000)
        partial_distance += 1000
    
    
    data_2 = []
    for i in range(1, len(partial_times)):
        data = (
                str(i).rjust(2), 
                #average_gradients[i-1],
                #str(datetime.timedelta(seconds = (partial_times[i] - partial_times[i-1])))[3:7],
                str(datetime.timedelta(seconds = partial_times[i]))[:7])
        data_2.append(data)
    all_data.append(data_2)
   
    '''
    if partial_distance < distances[-1]:
        if pront_to_stdout == True:
            print('finish time: %skm, %sh' % (float(distances[-1])/1000, str(datetime.timedelta(seconds = total_time))[:7]))
    '''
    
    #split times pro 5 kilometer
    
    partial_times = [0]
    partial_time = 0
    section = 0
    distance_used = 0
    height_start = heights[0]
    #average_gradients = []
    partial_distance = 0
    while partial_distance <= distances[-1]-5000:
        section_begin = section
        distance_used_begin = distance_used
        section_distance = 0
        while section < len(partial_distances) and partial_distances[section] - distance_used <= 5000 - section_distance:
            partial_time += paces_per_section[section]*(partial_distances[section] - distance_used)
            section_distance += (partial_distances[section] - distance_used)
            distance_used = 0
            section += 1
        if section_distance < 5000:
            partial_time += paces_per_section[section]*(5000 - section_distance)
            distance_used += (5000 - section_distance)
        partial_times.append(int(partial_time))
   
        if section == len(partial_distances):
            section -= 1
        height_end = heights[section] + (float(distance_used) / partial_distances[section]) * height_differences[section]
        height_start = heights[section_begin] + (float(distance_used_begin) / partial_distances[section_begin]) * height_differences[section_begin]
    
        #average_gradients.append(100*float(height_end-height_start)/5000)
        partial_distance += 5000
    data_3 = [] 
    for i in range(1, len(partial_times)):
        data =(
                str(5*i).rjust(2), 
                #average_gradients[i-1],
                #str(datetime.timedelta(seconds = (partial_times[i] - partial_times[i-1])/5))[:7],
                str(datetime.timedelta(seconds = partial_times[i]))[:7])
        data_3.append(data)
    all_data.append(data_3)
    print("data_3")
    print(data_3)
    '''
    if partial_distance < distances[-1]:
        if pront_to_stdout == True:
            print('finish time: %skm, %sh' % (float(distances[-1])/1000, str(datetime.timedelta(seconds = total_time))[:7]))
    '''
    
    # split times pro markantem punkt
   
    '''
    f = open('sections_marathon_la_paz_markante_punkte.csv', 'r')
    markant_distances = [0]
    markant_names = ['start']
    for l in f:
        (name, dist) = l.split(',')
        markant_distances.append(int(dist.strip()))
        markant_names.append(name.strip())
    f.close()
    '''
    partial_markant_distances = [markant_distances[i+1]-markant_distances[i] for i in range(len(markant_distances)-1)]
    
    partial_times = [0]
    partial_time = 0
    section = 0
    section_markant = 0
    distance_used = 0
    height_start = heights[0]
    #average_gradients = []
    partial_distance = 0
    while partial_distance < markant_distances[-1]:
        section_begin = section
        distance_used_begin = distance_used
        section_distance = 0
        while section < len(partial_distances) and partial_distances[section] - distance_used < partial_markant_distances[section_markant] - section_distance:
            partial_time += paces_per_section[section]*(partial_distances[section] - distance_used)
            section_distance += (partial_distances[section] - distance_used)
            distance_used = 0
            section += 1
        if section == len(paces_per_section):
            section -= 1
        if section_distance < partial_markant_distances[section_markant]:
            partial_time += paces_per_section[section]*(partial_markant_distances[section_markant] - section_distance)
            distance_used += (partial_markant_distances[section_markant] - section_distance)
        partial_times.append(int(partial_time))
    
        height_end = heights[section] + (float(distance_used) / partial_distances[section]) * height_differences[section]
        height_start = heights[section_begin] + (float(distance_used_begin) / partial_distances[section_begin]) * height_differences[section_begin]
    
        #average_gradients.append(100*float(height_end-height_start)/partial_markant_distances[section_markant])
        partial_distance += partial_markant_distances[section_markant]
        section_markant += 1
    
    
    data_4 = []  
    for i in range(1, len(partial_times)):
        if partial_times[i]%60 >= 30:
            partial_times[i] += 60
        data = (
                float(markant_distances[i])/1000, 
                #average_gradients[i-1],
                #str(datetime.timedelta(seconds = (partial_times[i] - partial_times[i-1])*1000/partial_markant_distances[i-1]))[3:7],
                #str(datetime.timedelta(seconds = partial_times[i]))[:7],
                str(datetime.timedelta(seconds = partial_times[i]))[:4],
                markant_abbr[i])
        data_4.append(data)
    all_data.append(data_4)
    '''
    if partial_distance < distances[-1]:
        if pront_to_stdout == True:
            print('finish time: %skm, %sh' % (float(distances[-1])/1000, str(datetime.timedelta(seconds = total_time))[:7]))
    '''
    if pdf:
        create_pdf(tex_file_name, name, total_time, all_data)
    if stdout:
        print_to_stdout(all_data)

def create_pdf(file_name, name, total_time, all_data):
    fout = open(file_name + '.tex','w')
    fout.write('\\documentclass[letterpaper]{article}\n')
    fout.write('\\usepackage[margin=1in]{geometry}\n')
    fout.write('\\usepackage[utf8]{inputenc}\n')
    fout.write('\\usepackage{graphicx}\n')
    fout.write('\\begin{document}\n')
    fout.write('\\begin{center}')
    fout.write('{\\huge Split times - ' + name + '\\\\Target time: ' + str(datetime.timedelta(seconds = total_time))[:4] + 'h}\\\\[0.5cm]\n')

    fout.write('{\\Large Uphill and downhill sections}\\\\[0.5cm]\n')    
    fout.write('\\begin{tabular}{|c|c|c|c|c|c|c|}\n')
    fout.write('\\hline Total & Partial & Gradient & Pace & Section time & Split time & Location\\\\ \\hline\n')
    for data in all_data[0]:
        if type(data[2]) == str:
            fout.write(' {0:4.1f} km & {1:4.1f} km & {2} \\%& {3} min/km & {4} & {5} &  {6}\\\\ \n'.format(*data))
        else:
            fout.write(' {0:4.1f} km & {1:4.1f} km & {2:.1f} \\%& {3} min/km & {4} & {5} &  {6}\\\\ \n'.format(*data))
    fout.write('\\hline\n')
    fout.write('\\end{tabular}\n')

    fout.write('{\\\\[0.5cm]\\Large Split times per kilometer / per 5 kilometers / per notorious location}\\\\[0.5cm]\n')
    fout.write('\\begin{minipage}{0.4\\textwidth}\n')
    fout.write('\\begin{minipage}{0.4\\textwidth}\n')
    fout.write('\\center\\begin{tabular}{|c|c|}\n')
    fout.write('\\hline Km & Time\\\\ \\hline\n')
    for (i,data) in enumerate(all_data[1]):
        if i == len(all_data[1])/2 + 1:
            fout.write('\\hline\n')
            fout.write('\\end{tabular}\n')
            fout.write('\\end{minipage}\n')
            fout.write('\\begin{minipage}{0.4\\textwidth}\n')
            fout.write('\\center\\begin{tabular}{|c|c|}\n')
            fout.write('\\hline Km & Time\\\\ \\hline\n')
        fout.write(' %s & %s \\\\ \n' % data)
    fout.write('\\hline\n')
    fout.write('\\end{tabular}\n')
    fout.write('\\end{minipage}\n')
    fout.write('\\end{minipage}\n')
    fout.write('\\begin{minipage}{0.2\\textwidth}\n')
    #fout.write('{\\Large Split times each 5 kilometers}\\\\[0.5cm]\n')
    fout.write('\\begin{tabular}{|c|c|}\n')
    fout.write('\\hline Km & Time\\\\ \\hline\n')
    for data in all_data[2]:
        fout.write(' %s & %s \\\\ \n' % data)
    fout.write('\\hline\n')
    fout.write('\\end{tabular}\n')
    fout.write('\\end{minipage}\n')
    fout.write('\\begin{minipage}{0.3\\textwidth}\n')
    #fout.write('{\\Large Split times per distinctive spot}\\\n')
    fout.write('\\center\\begin{tabular}{|c|c|c|}\n')
    fout.write('\\hline Km & Time & Location\\\\ \\hline\n')
    for data in all_data[3]:
        fout.write(' %4.1f & %s & %s\\\\ \n' % data)
    fout.write('\\hline\n')
    fout.write('\\end{tabular}\n')
    fout.write('\\end{minipage}\n')
    
    fout.write('\\end{center}\n')
    fout.write('\\end{document}')
    fout.close()
    os.system('pdflatex ' + file_name + '.tex')
    print('written to ' + file_name + '.pdf')
    #os.system('rm {0}.aux {0}.log {0}.tex'.format(file_name))
    '''
    if createDVI:
        print(output_file + '.dvi created.')
        if launchDVI:
            subprocess.Popen(['xdvi',output_file + '.dvi'])
    if create_pdf:
        os.system('pdflatex ' + output_file)
        os.system('rm *.aux *.log')
        print(output_file + '.pdf created.')
        if launchPDF:
            subprocess.Popen(['evince',output_file + '.pdf'])
    '''

def print_to_stdout(all_data):
    print('#'*50)
    print('#                   per section                  #')
    print('#'*50)
    print
    print('   #   | part dst | sct dst  | gradient  |  pace  | sct tme | part tme | location')
    print('-'*90)
    for data in all_data[0]:
        if type(data[2]) == str:
            print('     {0:4.1f} km  | {1} km  | {2}  |  {3}  | {4} | {5}  | {6}'.format(*data))
        else:
            print('     {0:4.1f} km  | {1:4.1f} km  | {2:.1f} % |  {3}  | {4} | {5}  | {6}'.format(*data))
            #print('     %4.1f km  | %4.1f km  | % .1f %% |  %s  | %s | %s  | %s' % data)
    #split times per kilometer
    print
    print('#'*50)
    print('#                   per kilometer                #')
    print('#'*50)
    print

    print(' part dst |  gradient  |  pace  | part tme')
    print('-'*50)
    for data in all_data[1]:
        print('   {} km | {}'.format(*data))

    print
    print('#'*50)
    print('#                   pro 5 kilometer              #')
    print('#'*50)
    print
    print(' part dst |  gradient  |  pace  | part tme')
    print('-'*50)
    for data in all_data[2]:
        print('   {} km  |  {}'.format(*data))
    print
    print('#'*50)
    print('#                pro markantem punkt             #')
    print('#'*50)
    print
    print(' dst  | time | name')
    print('-'*25)
    for data in all_data[3]:
        print(' %4.1f | %s | %s' % data)


if __name__ == '__main__':
    main()
