repositories = ['bat', 'bowtie2']

#sort repositories
file = open("README.md", "w")

file.write( '| Name | Information |\n' )
file.write( '| --- | --- |\n' )

for repository in repositories:
  str = '| [' + repository + '](http://github.com/pscedu/singularity-' + repository + ') | ![Status](https://github.com/pscedu/singularity-' + repository + '/actions/workflows/main.yml/badge.svg)![Issue](https://img.shields.io/github/issues/pscedu/singularity-' + repository + ')![forks](https://img.shields.io/github/forks/pscedu/singularity-' + repository + ')![Stars](https://img.shields.io/github/stars/pscedu/singularity-' + repository + ')![License](https://img.shields.io/github/license/pscedu/singularity-' + repository + ') |\n'
  file.write( str )

file.close()
