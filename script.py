#List repositories
repositories = ['bat', 'bowtie2','fastani','phylip-suite','blast','bwa','picard','gatk','hisat2','abyss','trimmomatic','graphviz','hyperfine','dust','tiger','gent','asciinema','trimmomatic','methylpy','octave']

#sort repositories
epositories.sort()

for repository in repositories:
    new_string = string.replace(  "#| [repository](http://github.com/pscedu/singularty-"+str(repository),") |![Status](https://github.com/pscedu/singularity-"+str(repository),"/actions/workflows/main.yml/badge.svg)![Issue](https://img.shields.io/github/issues/pscedu/singularity-"+str(repository),")![forks](https://img.shields.io/github/forks/pscedu/singularity-"+str(repository),")![Stars](https://img.shields.io/github/stars/pscedu/singularity-"+str(repository),")![License](https://img.shields.io/github/license/pscedu/singularity-"+str(repository),") |
)"
    new_strings.append(new_string)
print (new_strings)
