#sort repositories
file = open("README.md", "w")

# STEM
repositories = ['bowtie2','spades','blast','bowtie2','fastqc','sra-toolkit','gatk','hmmer','bcftools','raxml','spades','busco','samtools','bedtools','bamtools','fastani','phylip-suite','blast','viennarna','cutadapt','bismark','star','prodigal','bwa','picard','hisat2','abyss','octave','trimmomatic','tiger','gent','methylpy','fasttree','vcf2maf','htslib','kraken2','aspera-connect','trimmomatic']
repositories.sort()
file.write('# List of Singularity containers\n')
file.write('## STEM\n')
file.write( '| Name | Information |\n' )
file.write( '| --- | --- |\n' )

for repository in repositories:
  str = '| [' + repository + '](http://github.com/pscedu/singularity-' + repository + ') | ![Status](https://github.com/pscedu/singularity-' + repository + '/actions/workflows/main.yml/badge.svg)![Status](https://github.com/pscedu/singularity-' + repository + '/actions/workflows/pretty.yml/badge.svg)![Issue](https://img.shields.io/github/issues/pscedu/singularity-' + repository + ')![forks](https://img.shields.io/github/forks/pscedu/singularity-' + repository + ')![Stars](https://img.shields.io/github/stars/pscedu/singularity-' + repository + ')![License](https://img.shields.io/github/license/pscedu/singularity-' + repository + ') |\n'
  file.write( str )

# Utilities
repositories = ['graphviz','browsh','hyperfine','dust','gnuplot','pandoc','mc','bat','flac','visidata','octave','ncdu','lazygit','asciinema','ffmpeg','imagemagick','rclone']
repositories.sort()
file.write('\n## Utilities\n')
file.write( '| Name | Information |\n' )
file.write( '| --- | --- |\n' )

for repository in repositories:
  str = '| [' + repository + '](http://github.com/pscedu/singularity-' + repository + ') | ![Status](https://github.com/pscedu/singularity-' + repository + '/actions/workflows/main.yml/badge.svg)![Status](https://github.com/pscedu/singularity-' + repository + '/actions/workflows/pretty.yml/badge.svg)![Issue](https://img.shields.io/github/issues/pscedu/singularity-' + repository + ')![forks](https://img.shields.io/github/forks/pscedu/singularity-' + repository + ')![Stars](https://img.shields.io/github/stars/pscedu/singularity-' + repository + ')![License](https://img.shields.io/github/license/pscedu/singularity-' + repository + ') |\n'
  file.write( str )

file.close()
