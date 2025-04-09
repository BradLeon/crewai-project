#!/usr/bin/env python
import sys
import warnings

from datetime import datetime

from content_creation_social_media.crew import ContentCreationSocialMedia

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information
import textwrap

def run():
    """
    Run the crew.
    """
    inputs = {
        'subject': '如何看待deepseek模式的成功对于Nvidia股价是利空这种观点"'
    }
    
    try:
        print("Starting crew execution...")
        result = ContentCreationSocialMedia().crew().kickoff(inputs=inputs)
    except Exception as e:
        print(f"Error details: {str(e)}")
        print(f"Error type: {type(e)}")
        if hasattr(e, '__cause__'):
            print(f"Caused by: {e.__cause__}")
        raise Exception(f"An error occurred while running the crew: {e}")
    
    posts = result.pydantic.dict()['social_media_posts']
    for post in posts:
            platform = post['platform']
            content = post['content']
            print(platform)
            wrapped_content = textwrap.fill(content, width=50)
            print(wrapped_content)
            print('-' * 50)
        
    print('--------article---------')
    print(result.pydantic.dict()['article'])

def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = {
        'subject': 'Predict the top ten performance breakout stocks in the AI Agent field in 2025'
    }
    try:
        ContentCreationSocialMedia().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")

def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        ContentCreationSocialMedia().crew().replay(task_id=sys.argv[1])

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")

def test():
    """
    Test the crew execution and returns the results.
    """
    inputs = {
        'subject': 'Predict the top ten performance breakout stocks in the AI Agent field in 2025'
    }
    try:
        ContentCreationSocialMedia().crew().test(n_iterations=int(sys.argv[1]), openai_model_name=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")
