# Brat Annotation Generator from CoNLL09 Semantic Role Labels
This is an experimental program that converts semantic role labels in a CoNLL2009 format text file into Brat annotation format.

Note that it still contains bugs.

## Requirements
nltk MosesDetokenizer

Just install "perluniprops" package  
\>\> import nltk  
\>\> nltk.download('perluniprops')


## Usage
$python3 conll09\_to\_brat.py test.txt

Option:

- -o FILENAME  
The program outputs Brat annotations to a file. If you don't use this option, the program will display Brat annotations to your console.

- -a FILENAME  
The program generates additional Brat annotations to the given file. If you already have an annotation file for a text and want to add semantic role labels to it, use this option with "-o" option.


If you visualize with Brat, you will get like this.
![Image](https://i.imgur.com/Tcc9o2R.png "Sample")

## License
Apache License 2.0

