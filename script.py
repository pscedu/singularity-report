#sort repositories
file = open("README.md", "w")

# STEM
repositories = ['bowtie2','prodigal','samtools','fastani','phylip-suite','blast','viennarna','cutadapt','bismark','star','prodigal','bwa','picard','hisat2','abyss','octave','trimmomatic','tiger','gent','methylpy','fasttree','vcf2maf','htslib','aspera-connect','trimmomatic']
repositories.sort()
file.write('# List of Singularity containers\n')
file.write('## STEM\n')
file.write( '| Name | Information |\n' )
file.write( '| --- | --- |\n' )

for repository in repositories:
  str = '| [' + repository + '](http://github.com/pscedu/singularity-' + repository + ') | ![Status](https://github.com/pscedu/singularity-' + repository + '/actions/workflows/main.yml/badge.svg)![Issue](https://img.shields.io/github/issues/pscedu/singularity-' + repository + ')![forks](https://img.shields.io/github/forks/pscedu/singularity-' + repository + ')![Stars](https://img.shields.io/github/stars/pscedu/singularity-' + repository + ')![License](https://img.shields.io/github/license/pscedu/singularity-' + repository + ') |\n'
  file.write( str )

# Utilities
repositories = ['bat','graphviz','hyperfine','dust','asciinema','ffmpeg','imagemagick','rclone','ffmpeg']
repositories.sort()
file.write('\n## Utilities\n')
file.write( '| Name | Information |\n' )
file.write( '| --- | --- |\n' )

for repository in repositories:
  str = '| [' + repository + '](http://github.com/pscedu/singularity-' + repository + ') | ![Status](https://github.com/pscedu/singularity-' + repository + '/actions/workflows/main.yml/badge.svg)![Issue](https://img.shields.io/github/issues/pscedu/singularity-' + repository + ')![forks](https://img.shields.io/github/forks/pscedu/singularity-' + repository + ')![Stars](https://img.shields.io/github/stars/pscedu/singularity-' + repository + ')![License](https://img.shields.io/github/license/pscedu/singularity-' + repository + ') |\n'
  file.write( str )

file.close()
