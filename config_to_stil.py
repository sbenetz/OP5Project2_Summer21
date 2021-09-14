import sys
file = sys.argv[1]
with open(file,'r') as reader:
    with open(file+'.stil','w') as writer:
        writer.write('Signals {\n')
        contents = reader.read()
        confs = contents[contents.find('CONF'):]
        lines = confs.split('\n')
        for line in lines:
            group = None
            if line.startswith('CONF I,'):
                group = line[line.find('(')+1:line.rfind(')')]
                group = group.split(',')
                writer.write(' In; \n'.join(group)+' In; \n')
            elif line.startswith('CONF O,'):
                group = line[line.find('(')+1:line.rfind(')')]
                group = group.split(',')
                writer.write(' Out; \n'.join(group)+' Out; \n')
            elif line.startswith('CONF IO,'):
                group = line[line.find('(')+1:line.rfind(')')]
                group = group.split(',')
                writer.write(' InOut; \n'.join(group)+' InOut; \n')
        writer.write('}')
        