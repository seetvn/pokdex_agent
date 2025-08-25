def print_observation(observation):
    print (" - -  - OBSERVATION from TOOL - - - ")
    print('=======================================')
    # print(observation)
    for key,value in observation.items():
        print(f"{key}: {value}")
        print('----------------------------------------')
    return