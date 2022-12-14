from re import L
import pandas as pd 
import os
import matplotlib.pyplot as plt
from general_functions import * 
import plotly.express as px

os.chdir(r"C:\Users\vince\Documents\thesis\data\events")


"""
    This method filters dataset based on pre-defined filter, using challenge and problem names
    Inputs: 
        file: Name of the file
        challenge_name: Name of the challenge
        problem_name: Name of the problem 
"""
def filter(file, challenge_name, problem_name):
    df = pd.read_csv(file)
    filtered_df = df[(df.challenge_name == challenge_name) & (df.problem_name == problem_name)] 
    return filtered_df


"""
    This function returns a dictionary of students; keys are student IDs and  values are another dictionary where 
    keys are problems attempted by student and values are events completed by student

    Input: Filename of the dataset and name of the challenge
    Output: Dictionary of students
"""
def get_student_problem_interactions(file, challenge_name):
    os.chdir(r"C:\Users\vince\Documents\thesis\data\raw_data\events")

    # Filtered dataset
    df = filter(file, challenge_name)

    # Dictionary that will be returned
    students = {} 

    # Iterate through rows of filtered dataset
    for row in df.itertuples():

        # Retrieve name of current student 
        current_student = row.user_id
        if current_student not in students:
            students[current_student] = {}
        
        # Retrieve name of current problem  
        problem_name = row.challenge_name + "-" + row.problem_name + "-" + str(row.slide_no)
        if problem_name not in students[current_student]:
            students[current_student][problem_name] = []

        # Assign event to list corresponding to current problem
        students[current_student][problem_name].append(row.event_name)

    return students

"""
    This function plots bar charts showing the frequency of problem sequences and interaction sequences
    for the given module (which belongs to a specific challenge)
"""
def plot_results(final_outcomes_dict, final_sequences_dict, problem_name):
    plt.bar([str(key) for key in final_outcomes_dict.keys()], final_outcomes_dict.values())
    plt.title("Distribution of problem outcomes for Module {}".format(problem_name))
    plt.xlabel("Outcomes")
    plt.ylabel("Count")
    plt.show()

    plt.bar([str(key) for key in final_sequences_dict.keys()], final_sequences_dict.values())
    plt.title("Distribution of interaction sequences for Module {}".format(problem_name))
    plt.xlabel("Interaction sequence")
    plt.ylabel("Count")
    plt.show()


"""
    This function aggregates all outcomes that do not appear as frequently
    into a separate category called "Other"
"""
def aggregate(outcomes_dict, sequences_dict, num_students):
    final_outcomes_dict = {}
    for outcome in outcomes_dict:
        if outcomes_dict[outcome] < num_students/10:
            if "Other" not in final_outcomes_dict:
                final_outcomes_dict["Other"] = outcomes_dict[outcome]
            else:
                final_outcomes_dict["Other"] += outcomes_dict[outcome]
        else:
            final_outcomes_dict[outcome] = outcomes_dict[outcome]

    # Aggregate all sequences that do not appear as frequently
    # into a separate category called "Other"
    final_sequences_dict = {}
    for sequence in sequences_dict:
        if sequences_dict[sequence] < num_students/20:
            if "Other" not in final_sequences_dict:
                final_sequences_dict["Other"] = sequences_dict[sequence]
            else:
                final_sequences_dict["Other"] += sequences_dict[sequence]
        else:
            final_sequences_dict[sequence] = sequences_dict[sequence]

    return final_outcomes_dict, final_sequences_dict


"""
    This function returns two dictionaries: one containing the counts of different interaction sequences for
    the module, and the other containing the counts of problem outcomes for the module. 

    Inputs: 
        student_dict: A dictionary containing interaction sequences for each student in the module 
        problem_slides: A list of indices representing problem slides in the module 

    Returns:
        outcomes_dict: A dictionary containing counts of different problem outcomes for the module
        sequences_dict: A dicitonary containing counts of different interaction sequences for the module 
"""
def get_results_dicts(student_dict, problem_slides):
    # Dictionary to store the outcome tuples and their 
    # corresponding counts 
    outcomes_dict = {}

    # Dictionary to store the interaction sequences and their 
    # corresponding counts 
    sequences_dict = {}

    for student in student_dict:
        entry = student_dict[student] 
        sequence = tuple(entry)
        if sequence not in sequences_dict:
            sequences_dict[sequence] = 1
        else:
            sequences_dict[sequence] += 1
        
        # Indices of the first pair of problem slides 
        idx0 = problem_slides[0]
        idx1 = problem_slides[1]
        
        # Indices of the second pair of problem slides 
        idx2 = problem_slides[2]
        idx3 = problem_slides[3]

        outcome = tuple(entry[idx0:idx1+1] + entry[idx2:idx3+1]) 
        if outcome not in outcomes_dict:
            outcomes_dict[outcome] = 1
        else:
            outcomes_dict[outcome] += 1
    
    return outcomes_dict, sequences_dict


"""
    This method determines interaction sequences for a given module for all students who have participated 
    in the module

    Inputs: 
        df: A filetered dataframe representing all records for a module in a particular specific challenge 
        num_slides: Number of slides in the module
        problem_slides: A list of indices representing problem slides in the module 
        challenge_name: Name of the challenge

    Returns: 
        student_dict: A dictionary containing student IDs as keys, and their interaction sequences for the module as values.
"""
def get_student_dict(df, num_slides, problem_slides, challenge_name):
    student_dict = {}

    # The ID of the first student 
    student = df.iloc[0].user_id

    # Create the interaction string for each student
    # By default, this will have all 0s for interactive slides
    # and Ns for problem slides 
    interaction_string = [0]*num_slides
    for slide_no in problem_slides:
        interaction_string[slide_no] = "N"

    # Store the interaction string as the value of the dictionary
    student_dict[student] = interaction_string

    # Iterate through the rows of the dataframe
    for row in df.itertuples():

        # We have encountered a new student
        if row.user_id != student:

            # Assign the current student's ID to the student variable
            student = row.user_id

            # Construct the default interaction string for each student
            # This consists of 0s where there is an interaction slide
            # and Ns where there is a problem slide 
            interaction_string = [0]*num_slides
            for slide_no in problem_slides:
                interaction_string[slide_no] = "N"

            # Store the interaction string as the value of the dictionary
            student_dict[student] = interaction_string

        # We have encountered a slide steps complete event for an interactive slide 
        if row.event_name == "slide_steps_complete" and row.slide_no not in problem_slides: 
            student_dict[student][row.slide_no] = 1

        # We have encountered a problem failed event for a problem slide 
        elif row.event_name == "problem_failed" and row.slide_no in problem_slides:

            # Only update the slide's status to fail if the student had not 
            # already passed the slide before 
            if student_dict[student][row.slide_no] != "P":
                student_dict[student][row.slide_no] = "F" 

        # We have encountered a problem passed event for a problem slide
        elif row.event_name == "problem_passed" and row.slide_no in problem_slides:
            student_dict[student][row.slide_no] = "P" 

        elif row.event_name == "run_inline" and challenge_name != "challenge-newbies-2018" and row.slide_no not in problem_slides:
            student_dict[student][row.slide_no] = 1
        
    return student_dict

""""
    This method determines the problem slides in a particular module
    Inputs: 
        df: A filtered dataframe representing all records/interactions for a given module 
        challenge_name: The name of the challenge for the module
    Returns:
        problem_slides: A list of indices for problem slides
"""
def get_problem_slides(df, challenge_name):
    
    # For each challenge, set thresholds according to determined values 
    if challenge_name == "challenge-beginners-blockly-2018":
        limit = 100
    elif challenge_name == "challenge-newbies-2018":
        limit = 50
    elif challenge_name == "challenge-advanced-2018":
        limit = 50
    else:
        limit = 500

    problem_slides = []

    # Filter the dataset and retain all records that have a
    # problem_passed event
    problem_df = df[(df.event_name == "problem_passed")]  
    for slide_no in problem_df["slide_no"].unique():

        # Note: Some interactive slides are mislabelled as problem slides. To account
        # for this, take the problem slides that have a high rate of visits from users
        if len(problem_df[(problem_df.slide_no == slide_no)]) > limit:
            problem_slides.append(slide_no)
    
    # Sort the list so that the indices are in ascending order 
    problem_slides.sort()

    # Sense check the problem slides 
    print("The problem slides are {}".format(problem_slides))

    return problem_slides

 
"""
    This function calculates the number of times a slide in a particular module (e.g. w1p1) was viewed by students
    in that module.

    Inputs:
        student_dict: A dictionary of interaction sequences for students for a particular module
    Returns:
        slide_completion_dict: A dictionary of slides and the number of times they were completed by students enrolled in the module
"""
def get_slide_completion_dict(student_dict):

    slide_completion_dict = {}

    # Student dict is for a particular module 
    for student in student_dict:

        for i in range(len(student_dict[student])):
            # Slide was completed 
            if student_dict[student][i] == 1:
                if i not in slide_completion_dict:
                    slide_completion_dict[i] = 1
                else:
                    slide_completion_dict[i] += 1
        
    return slide_completion_dict 

                     
"""
    This method plots the number of times a slide was completed (slide completion rate) against the slide number 
    across all 10 modules.
"""
def slide_completion_plots(challenge_name):

    # Load the file 
    file = 'events_processed.csv'

    # Read the file into a dataframe 
    df = pd.read_csv(file)

    # Specify a list of problem names - note: w3p1 is really w3p1
    if challenge_name == "challenge-newbies-2018":
        problem_names = ["w1p1", "w1p2", "w2p1", "w2p2", "w3p1n", "w3p2", "w4p1", "w4p2", "w5p1", "w5p2"]
    else:
        problem_names = ["w1p1", "w1p2", "w2p1", "w2p2", "w3p1", "w3p2", "w4p1", "w4p2", "w5p1", "w5p2"]
    fig, ax = plt.subplots(2, 5, sharey=True, sharex=True)

    # Use two indices to represent the subplots. i represents the vertical index, and j represents 
    # the horizontal index in the subplot
    i = 0 
    j = 0

    # Go through each particular problem
    for problem_name in problem_names:

        if challenge_name == "challenge-newbies-2018":
            df = df[df.user_id != "c5efdcfda95bd5fdfcfe6b1a2a2eb737"]
            df = df[df.user_id != "d1265ffa37786b49a23a505905db4536"]
            df = df[df.user_id != "cd7f9726bee1d15be9a0a4972f1013fb"]
            df = df[df.user_id != "264a2b917ba86bdbc8be12c2540fed37"]

        # Retrieve the student records that correspond to the challenge and problem names specified
        df = filter(file, challenge_name, problem_name)

        # The number of slides in the module (+1 to account for 0-indexing)
        num_slides = df["slide_no"].max() + 1  
        problem_slides = get_problem_slides(df, challenge_name)

        # Sort the dataset by users 
        df = df.sort_values(by=['user_id'])  

        # Retrieve the dictionary of student IDs (keys) and their sequences for the given module 
        student_dict = get_student_dict(df, num_slides, problem_slides, challenge_name)

        # Retrieve the dictionary of slide numbers (keys) and the number of times that slide was attempted by students (values)
        slide_completion_dict = get_slide_completion_dict(student_dict)

        # Plot the slide completion graph for the given problem e.g. w1p1
        ax[i, j].bar(slide_completion_dict.keys(), slide_completion_dict.values())
        if problem_name == "w3p1n":
            problem_name = "w3p1"
        ax[i, j].set_title(problem_name)

        # Move on to the next subplot 
        j += 1 
        if j == 5:
            j = 0
            i += 1

    for a in ax.flat:
        a.label_outer()

    fig.suptitle("Slide completion rates across all modules for {}".format(challenge_name))
    fig.supxlabel("Slide number")
    fig.supylabel("Frequency")
    plt.savefig("slide_completion_all_modules.jpg")
    plt.show()
   

"""
    This method determines and returns a list of default interaction sequences across all modules for a given challenge
    Input: Name of the challenge
    Returns: A list of default interaction sequences (all 0s for interactive slides and all Ns for problem slides)
"""
def get_default_sequences(challenge_name):

    file = 'events_processed.csv'
    df = pd.read_csv(file) 
    if challenge_name == "challenge-newbies-2018":
        problem_names = ["w1p1", "w1p2", "w2p1", "w2p2", "w3p1n", "w3p2", "w4p1", "w4p2", "w5p1", "w5p2"]
    else:
        problem_names =  ["w1p1", "w1p2", "w2p1", "w2p2", "w3p1", "w3p2", "w4p1", "w4p2", "w5p1", "w5p2"]
    default_sequences = []

    # Iterate through all problems
    for i in range(len(problem_names)):

        problem_name = problem_names[i] 
        df = filter(file, challenge_name, problem_name)
        if challenge_name == "challenge-newbies-2018":
            df = df[df.user_id != "c5efdcfda95bd5fdfcfe6b1a2a2eb737"]
            df = df[df.user_id != "d1265ffa37786b49a23a505905db4536"]
            df = df[df.user_id != "cd7f9726bee1d15be9a0a4972f1013fb"]

        # The number of slides in the module (+1 to account for 0-indexing)
        num_slides = df["slide_no"].max() + 1  
        problem_slides = get_problem_slides(df, challenge_name)
        
        # Construct the default sequence
        default_sequence = [0]*num_slides
        for problem in problem_slides:

            # Mark the problem slides with an "N" to indicate non-completion by deafult
            default_sequence[problem] = "N"

        default_sequences.append(default_sequence)

    return default_sequences


"""
    This function determines and returns the important slides belonging to modules for a given challenge. The frequency
    thresholds by which a slide is determined as being important vary across modules and challenges.
    Returns: A dictionary containing module names (keys) and a list of important slides in the module (values)
    Note: This only works for challenge-newbies-2018 so far, due to the thresholds 
"""
def get_important_slides(challenge_name):
    file = 'events_processed.csv'
    df = pd.read_csv(file)
    problem_names = ["w1p1", "w1p2", "w2p1", "w2p2", "w3p1n", "w3p2", "w4p1", "w4p2", "w5p1", "w5p2"]
    important_slide_dict = {}
     
    for i in range(len(problem_names)):
        problem_name = problem_names[i]
        df = filter(file, challenge_name, problem_name)

        # The number of slides in the module (+1 to account for 0-indexing)
        num_slides = df["slide_no"].max() + 1  
        problem_slides = get_problem_slides(df, challenge_name)

        # Sort the dataset by users 
        df = df.sort_values(by=['user_id'])  

        student_dict = get_student_dict(df, num_slides, problem_slides, challenge_name)
        slide_completion_dict = get_slide_completion_dict(student_dict)

        unimportant_slides = []

        for slide in slide_completion_dict:
            if i < 5 and slide_completion_dict[slide] < 250:
                unimportant_slides.append(slide)
                 
            elif i >= 5 and slide_completion_dict[slide] < 50:
                unimportant_slides.append(slide)

        important_slides = list(set(slide_completion_dict.keys())-set(unimportant_slides))
        important_slide_dict[problem_name] = important_slides

    return important_slide_dict

"""
    This function plots bar charts for problem outcomes and interaction sequences for each problem within a given challenge
"""
def plot_problem_interaction_one_module(challenge_name):
    file = 'events_processed.csv'
    if challenge_name == "challenge-newbies-2018":
        problem_names = ["w1p1", "w1p2", "w2p1", "w2p2", "w3p1n", "w3p2", "w4p1", "w4p2", "w5p1", "w5p2"]
    else:
        problem_names =  ["w1p1", "w1p2", "w2p1", "w2p2", "w3p1", "w3p2", "w4p1", "w4p2", "w5p1", "w5p2"]

    for problem_name in problem_names:
        df = filter(file, challenge_name, problem_name)

        # The number of slides in the module (+1 to account for 0-indexing)
        num_slides = df["slide_no"].max() + 1  
        print("The number of slides in the module is {}".format(num_slides))

        problem_slides = get_problem_slides(df, challenge_name)

        # Sanity check to check how many people completed a particular slide
        problem_df = df[(df.event_name == "problem_passed") & (df.slide_no == problem_slides[0])] # useful check
        print("The number of students which completed the first problem slide is {}".format(len(problem_df["user_id"].unique())))

        # Sort the dataset by users 
        df = df.sort_values(by=['user_id'])  
        student_dict = {}

        # Check the number of students in the dataset 
        num_students = len(df["user_id"].unique())
        print("The number of students is {}".format(num_students))

        if challenge_name == "challenge-newbies-2018":
            df = df[df.user_id != "c5efdcfda95bd5fdfcfe6b1a2a2eb737"]
            df = df[df.user_id != "d1265ffa37786b49a23a505905db4536"]
            df = df[df.user_id != "cd7f9726bee1d15be9a0a4972f1013fb"]
        
        student_dict = get_student_dict(df, num_slides, problem_slides, challenge_name)
        outcomes_dict, sequences_dict = get_results_dicts(student_dict, problem_slides)
        final_outcomes_dict, final_sequences_dict = aggregate(outcomes_dict, sequences_dict, num_students)
        plot_results(final_outcomes_dict, final_sequences_dict, problem_name)
     
 
"""
    This function returns the interaction sequences and problem sequences for all students in the challenge, 
    across all modules within the challenge.

    Input:
        challenge_name: Name of the challenge
    Returns:    
        problem_sequence_dict: A dictionary containing problem sequences across all modules in the challenge for each student
        interaction_sequence_dict: A dictionary containing interaction sequences across all modules in the challenge for each student
"""
def get_interaction_dicts(challenge_name):
    
    file = 'events_processed.csv'
    df = pd.read_csv(file) 
    if challenge_name == "challenge-newbies-2018":
        problem_names = ["w1p1", "w1p2", "w2p1", "w2p2", "w3p1n", "w3p2", "w4p1", "w4p2", "w5p1", "w5p2"]
    else:
        problem_names = ["w1p1", "w1p2", "w2p1", "w2p2", "w3p1", "w3p2", "w4p1", "w4p2", "w5p1", "w5p2"]
        
    problem_sequence_dict = {}
    interaction_sequence_dict = {}
    default_sequences = get_default_sequences(challenge_name)
    
    # Iterate through all problems
    for i in range(len(problem_names)):
        problem_name = problem_names[i] 
        df = filter(file, challenge_name, problem_name)

        # Temp student dict contains student IDs as keys, and interaction sequences for 
        # the particular module only
        if challenge_name == "challenge-newbies-2018":
            df = df[df.user_id != "c5efdcfda95bd5fdfcfe6b1a2a2eb737"]
            df = df[df.user_id != "d1265ffa37786b49a23a505905db4536"]
            df = df[df.user_id != "cd7f9726bee1d15be9a0a4972f1013fb"]

        # The number of slides in the module (+1 to account for 0-indexing)
        num_slides = df["slide_no"].max() + 1  

        problem_slides = get_problem_slides(df, challenge_name)

        # Sort the dataset by users 
        df = df.sort_values(by=['user_id'])  

        temp_student_dict = get_student_dict(df, num_slides, problem_slides, challenge_name)

        # Iterate through all students in the module
        for student in temp_student_dict:
            current_interaction_sequence = temp_student_dict[student]

            # print("LENGTH OF INTERACTION SEQUENCE IS: {}".format(len(current_interaction_sequence)))

            # If the given student was not previously recorded
            # (i.e. first time student is interacting with the course)
            if student not in interaction_sequence_dict:

                # Construct the student's previous interactions (all 0s for preceding interaction slides and Ns for 
                # preceding problem slides)
                previous_sequence = []
                for j in range(i):                    
                    previous_sequence.extend(default_sequences[j])

                # The student's overall interaction sequence is the previous default interaction sequences
                # joined together with the current sequence for this module 
                interaction_sequence_dict[student] = previous_sequence + current_interaction_sequence

            else:
                # Extend the student's overall interaction sequence with the 
                # interaction sequence from this module
                interaction_sequence_dict[student].extend(current_interaction_sequence)

            # To construct a problem interaction sequence containing only problem slide interactions
            # remove all instances of 0s and 1s from the sequence
            current_problem_sequence = current_interaction_sequence

            if 0 in current_problem_sequence:
                current_problem_sequence = remove_all(current_problem_sequence, 0)
                
            if 1 in current_problem_sequence:
                current_problem_sequence = remove_all(current_problem_sequence, 1)
            
            # If this is the first time that the student has engaged with the course
            if student not in problem_sequence_dict:
                problem_sequence_dict[student] = ["N"]*4*i + current_problem_sequence  
            else:
                # Otherwise, extend the student's problem sequence by the current problem sequence
                problem_sequence_dict[student].extend(current_problem_sequence)

        # Go through all students in the course that have been previously recorded
        for student in problem_sequence_dict:

            # If the student did not attempt this module, add the default interaction sequences
            # and problem sequences
            if student not in temp_student_dict: 
                problem_sequence_dict[student].extend(["N"]*4)
                interaction_sequence_dict[student].extend(default_sequences[i])  
                
    return problem_sequence_dict, interaction_sequence_dict


def get_slide_count_data(challenge_name):
    
    # Retrieve the problem sequences and interaction sequences for all students
    problem_sequence_dict, interaction_sequence_dict = get_interaction_dicts(challenge_name)
    X = []
    Y = []

    for student in interaction_sequence_dict:
        sequence = interaction_sequence_dict[student]
        countP = sequence.count("P")
        Y.append(countP)
        count1 = sequence.count(1)
        X.append(count1)

    data = []
    for i in range(len(X)):
        data.append([X[i], Y[i]])
    df = pd.DataFrame(data, columns=["content", "problem"])
    df.to_csv("slide-completion-counts-{}".format(challenge_name))

os.chdir(r"C:\Users\vince\Documents\thesis\data\events")


"""
    This function produces the 2D histograms showing content slide completion against problem slide completion for all four streams
"""
def get_course_hist():
    challenges = ["challenge-newbies-2018", "challenge-beginners-blockly-2018", "challenge-beginners-2018", "challenge-intermediate-2018"]
    #fig, ax = plt.subplots(2, 2, sharey=True, sharex=True)
    fig, ax = plt.subplots(2, 2)

    for challenge in challenges:
        df = pd.read_csv("slide-completion-counts-{}.csv".format(challenge))
        X = []
        Y = []
        for row in df.itertuples():
            X.append(row.content_normalised)
            Y.append(row.problem_normalised)
        if challenge == "challenge-newbies-2018":
            i = 0
            j = 0
            challenge = "Newbies"
        elif challenge == "challenge-beginners-blockly-2018":
            i = 0
            j = 1
            challenge = "Beginners Blockly"
        elif challenge == "challenge-beginners-2018":
            i = 1
            j = 0
            challenge = "Beginners"
        elif challenge == "challenge-intermediate-2018":
            i = 1
            j = 1
            challenge = "Intermediate"

        h = ax[i,j].hist2d(X, Y)
        ax[i,j].set_title("{}".format(challenge))
        # ax[i,j].colorbar()
    
    fig.suptitle("Heat map of content slide and problem slide completion")
    fig.colorbar(h[3], ax=ax.ravel().tolist())
    fig.supxlabel("Percentage of content slides completed")
    fig.supylabel("Number of problem slides successfully passed")
    plt.savefig("slide_completion_heatmap.jpg")
    plt.show()

"""
    This function produces the 2D histograms showing content slide completion against problem slide completion for all modules within all streams 
"""
def get_module_hist():

    
    challenges = ["challenge-newbies-2018", "challenge-beginners-blockly-2018", "challenge-beginners-2018", "challenge-intermediate-2018"]
    fig, ax = plt.subplots(2, 2)

    for challenge in challenges:

   
        fig, ax = plt.subplots(2, 5, sharex=True, sharey=True)
        
        if challenge == "challenge-newbies-2018":
            problem_names = ["w1p1", "w1p2", "w2p1", "w2p2", "w3p1n", "w3p2", "w4p1", "w4p2", "w5p1", "w5p2"]
        else:
            problem_names = ["w1p1", "w1p2", "w2p1", "w2p2", "w3p1", "w3p2", "w4p1", "w4p2", "w5p1", "w5p2"]

        if challenge == "challenge-intermediate-2018":
            divider = 2
        else:
            divider = 4
        
        for i in range(2):
            for j in range(5):

                problem = problem_names[i*5+j]
                df = pd.read_csv("v2-{}-{}.csv".format(challenge, problem))
                X = []
                Y = []
                for row in df.itertuples():
                    
                    row_list = list(row)
                    num_content = len(row_list) - 4
                    if challenge == "challenge-newbies-2018" and problem == "w3p1n":
                        problem = "w3p1"
                    if challenge == "challenge-beginners-blockly-2018":
                        if problem == "w5p2":
                            divider = 3
                        elif problem == "w1p1":
                            divider = 5
                        else:
                            divider = 4
                    elif challenge == "challenge-intermediate-2018":
                        if problem in ["w1p2", "w2p1", "w3p2", "w4p2", "w5p1"]:
                            divider = 3
                        else:
                            divider = 2
                    elif challenge == "challenge-beginners-2018":
                        if problem == "w1p1":
                            divider = 5
                        else:
                            divider = 4
                    countPass = row_list.count("Pass")/divider * 100
                    Y.append(countPass)
                    countCompleted = row_list.count("Completed")/num_content * 100
                    X.append(countCompleted)
                
                h = ax[i,j].hist2d(X, Y)
                ax[i,j].set_title("{}".format(problem))
                
        for a in ax.flat:
            a.label_outer()
        if challenge == "challenge-newbies-2018":
            challenge = "Newbies"
        elif challenge == "challenge-beginners-blockly-2018":
            challenge = "Beginners Blockly"
        elif challenge == "challenge-beginners-2018":
            challenge = "Beginners"
        elif challenge == "challenge-intermediate-2018":
            challenge = "Intermediate"
        fig.suptitle("Heat map of content slide and problem slide completion for each module in {}".format(challenge))
        fig.supxlabel("Percentage of content slides completed")
        fig.supylabel("Number of problem slides successfully passed")
        fig.colorbar(h[3], ax=ax.ravel().tolist())
        plt.show()