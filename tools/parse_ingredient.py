#!/usr/bin/env python3

import argparse
import tempfile
import subprocess
import json
from nltk import pos_tag
from nltk.tokenize import word_tokenize

def extract_crf_features(string):
    """Extract features from string required by CRF model and return CRF++ compatible list
    
    Parameters
    ----------
    string : str
        Ingredient string to parse
    
    Returns
    -------
    list
        List of CRF++ formatted tokens and features
    
    """
    features = []
    tokens = word_tokenize(string)
    for i, (token, pos) in enumerate(pos_tag(tokens)):
        features.append(f'{token}\t{pos}\tI{i+1}')
    
    return '\n'.join(features)

def execute_model(features, model):
    """Execute CRF model using features
    
    Parameters
    ----------
    features : str
        String of features in CRF++ compatible format
    model : str
        Path to CRF++ model
    
    Returns
    -------
    str
        Output from model
    """
    with tempfile.NamedTemporaryFile(mode='w') as f:
        f.write(features)
        f.flush()
        return subprocess.check_output(['crf_test', '--model', model, f.name]).decode('utf-8')

def parse_ingredient(string, model):
    """Parse ingredient senetence using CRF model to return structured data
    
    Parameters
    ----------
    string : str
        Ingredient sentence to parse
    model : str
        Path to CRF++ model
    
    Returns
    -------
    dict
        Dictionary of structured data parsed from input string
    """
    features = extract_crf_features(string)
    crf_output = execute_model(features, model)

    tokens = crf_output.splitlines()
    quantity, unit, item, comment = [], [], [], []
    for tok in tokens:
        parts = tok.split('\t')
        if parts[-1].endswith('QTY'):
            quantity.append(parts[0])
        elif parts[-1].endswith('UNIT'):
            unit.append(parts[0])
        elif parts[-1].endswith('ITEM'):
            item.append(parts[0])
        elif parts[-1].endswith('COMMENT'):
            comment.append(parts[0])

    return {'string': string, 
            'quantity': ' '.join(quantity),
            'unit': ' '.join(unit),
            'item': ' '.join(item),
            'comment': ' '.join(comment)}

def parse_multiple_ingredients(file, model):
        """Parse multiple ingredients from text file.
        Each line of the file is one ingredient sentence
        
        Parameters
        ----------
        file : str
            Path to input file
        model : str
            Path to CRF++ model
        
        Returns
        -------
        list[dict]
            List of dictionaries of structured data parsed from input sentences
        """
        with open(file, 'r') as f:
            contents = f.read()
        
        parsed = []
        sentences = contents.splitlines()
        for sent in sentences:
            parsed.append(parse_ingredient(sent, model))

        return parsed        
 
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Parse ingredient into structured data')
    parser.add_argument('-s', '--string', help='Ingredient string to parse')
    parser.add_argument('-f', '--file', help='Path to file of ingredient strings to parse')
    parser.add_argument('-m', '--model', default='./models/model.crfmodel', help='Path to model')
    args = parser.parse_args()

    if args.string is not None:
        parsed = parse_ingredient(args.string, args.model)
        print(json.dumps(parsed, indent=2))
    elif args.file is not None:
        parsed = parse_multiple_ingredients(args.file, args.model)
        print(json.dumps(parsed, indent=2))