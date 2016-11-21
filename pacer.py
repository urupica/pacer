#!/usr/bin/env python3

import datetime, os, subprocess, sys, json, jinja2
from fractions import Fraction
from jinja2 import Template

'''
Usage: $ splittimes.py [input.json]

pdfs will be written to current directory
'''

def main():
    with open(sys.argv[1]) as input_data:
        json_data = json.loads(input_data.read())
        print("Course: " + json_data['name'])
        for target_time in json_data['target times']:
            print("Computing target time " + target_time + "...")
            hh, mm = map(int, target_time.split(':'))
            file_name = sys.argv[1]
            name = json_data['name']
            output_name = json_data['prefix']
            points = json_data['points']
            calculate_split_times(name, output_name, points, hh, mm)

def compute_between_indices(distances, partial_distances, height_differences, paces_per_section, partial_times, locations, i, j):
    data = []
    data.append(float(distances[i+1])/1000) # total distance
    data.append(float(partial_distances[i])/1000) # partial distance
    data.append(float(height_differences[i]*100)/partial_distances[i]) # gradient
    data.append(format_time(seconds = int(paces_per_section[i]*1000))) # pace
    data.append(format_time(int(paces_per_section[i]*partial_distances[i]))) # section time
    data.append(format_time(partial_times[i], True)) # total time
    data.append(locations[i+1]) # location
    return data

def format_time(seconds, force_hours=False, round_seconds=False):
    hours = seconds//3600
    seconds -= hours*3600
    minutes = seconds//60
    seconds -= minutes*60
    if round_seconds:
        if seconds >= 30:
            minutes += 1
        if minutes == 60:
            hours += 1
            minutes = 0
    if force_hours or hours > 0:
        if round_seconds:
            return '%d:%02d' % (hours, minutes)
        return '%d:%02d:%02d' % (hours, minutes, seconds)
    else:
        if round_seconds:
            return minutes
        return '%d:%02d' % (minutes, seconds)


def calculate_split_times(name, output_name, all_points, hours, minutes):
    points = 0
    distances = []
    heights = []
    locations = []
    locations_abbr = []
    markant_distances = []
    markant_names = []
    markant_abbr = []
    markant_sections = []
    anchor = []

    # key variable that computes the pace according to the gradient
    # higher value means higher difference between uphill and downhill speed
    alpha = Fraction(4,2)

    for (i, point) in enumerate(all_points):
        points += 1
        distances.append(int(1000*point['dist']))
        heights.append(point['alt'])
        if point['primary']:
            markant_sections.append(i)
            markant_distances.append(1000*float(point['dist']))
            markant_names.append(point['full name'])
            markant_abbr.append(point['short name'])
        locations_abbr.append(point['short name'])
        locations.append(point['full name'])
        anchor.append(point['anchor'])

    total_time = (hours*60 + minutes)*60

    tex_file_name = '{}_{:02d}_{:02d}'.format(output_name, hours, minutes)
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

    data_1 = [['0 km', '0 km' ,'\centercell{---}', '\centercell{---}' ,'0:00 min', '0:00:00 h',locations[0]]]
    for i in range(points - 1):
        computed_data = compute_between_indices(distances, partial_distances, height_differences, paces_per_section, partial_times, locations, i, i+1)
        data_1.append(list(map(lambda x: ('%.1f km' % x[1]) if x[0] <= 1 else ('%.1f \\%%' % x[1]) if x[0] == 2 else ('%s min/km' % x[1]) if x[0] == 3 else ('%s min' % x[1]) if x[0] == 4 else ('%s h' % x[1]) if x[0] == 5 else x[1], list(enumerate(computed_data)))))
    all_data.append(data_1)

    data_5 = []#['0 km', '0 km' ,'\centercell{---}', '\centercell{---}' ,'0:00 min', '0:00:00 h',locations[0]]]
    for i in range(points - 1):
        data = [float(distances[i + 1])/1000, 
                format_time(partial_times[i], True, True), 
                locations_abbr[i + 1]]
        data_5.append(data)


    all_data.append(data_5)
    partial_times = [0]
    partial_time = 0
    section = 0
    distance_used = 0
    height_start = heights[0]
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
    
        partial_distance += 1000
    
    
    data_2 = []
    for i in range(1, len(partial_times)):
        data = (
                str(i).rjust(2), 
                #str(datetime.timedelta(seconds = partial_times[i]))[:7])
                format_time(partial_times[i], True, True)) 
        data_2.append(data)
    all_data.append(data_2)
   
    #split times pro 5 kilometer
    
    partial_times = [0]
    partial_time = 0
    section = 0
    distance_used = 0
    height_start = heights[0]
    partial_distance = 0
    while partial_distance <= distances[-1] - 5000:
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
    
        partial_distance += 5000
    data_3 = [] 
    for i in range(1, len(partial_times)):
        data =(
                5*i,
                format_time(partial_times[i], True, True)) 
        data_3.append(data)
    all_data.append(data_3)
    
    # split times pro markantem punkt
   
    partial_markant_distances = [markant_distances[i+1]-markant_distances[i] for i in range(len(markant_distances)-1)]
    
    partial_times = [0]
    partial_time = 0
    section = 0
    section_markant = 0
    distance_used = 0
    height_start = heights[0]
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
    
        partial_distance += partial_markant_distances[section_markant]
        section_markant += 1
    
    
    data_4 = []  
    for i in range(1, len(partial_times)):
        data = (
                float(markant_distances[i])/1000, 
                format_time(partial_times[i], True, True),
                markant_abbr[i])
        data_4.append(data)
    all_data.append(data_4)
    

    data_6 = []
    for i in range(points):
        data_6.append((float(distances[i])/1000, heights[i], locations_abbr[i], anchor[i]))
    all_data.append(data_6)

    create_pdf(tex_file_name, name, hours, minutes, all_data)

def create_pdf(file_name, name, hours, minutes, all_data):
    latex_jinja_env = jinja2.Environment(
	block_start_string = '\BLOCK{',
	block_end_string = '}',
	variable_start_string = '\VAR{',
	variable_end_string = '}',
	comment_start_string = '\#{',
	comment_end_string = '}',
	line_statement_prefix = '%%',
	line_comment_prefix = '%#',
	trim_blocks = True,
	autoescape = False,
	loader = jinja2.FileSystemLoader(os.path.dirname(os.path.abspath(sys.argv[0])))
    )
    #pathname = os.path.dirname(sys.argv[0])
    #template_path = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), 'template.tex')
    #template = latex_jinja_env.get_template(template_path)
    template = latex_jinja_env.get_template('template.tex')
    print("output: " + file_name + '.tex')
    fout = open(file_name + '.tex','w')
    fout.write(template.render(
        name = name, 
        hours = hours, 
        minutes = minutes, 
        data1 = all_data[0], 
        data2 = all_data[2], 
        data3 = all_data[3], 
        data4 = all_data[4], 
        data5 = all_data[1],
        data6 = all_data[5]))
    fout.close()

    os.system('rubber -d %s.tex' % file_name)
    os.system('rubber --clean ' + file_name)
    os.system('rm %s.tex' % file_name)
    print('written to ' + file_name + '.pdf')


if __name__ == '__main__':
    main()
