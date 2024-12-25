from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
import re
import json
from langchain_groq import ChatGroq

app = Flask(__name__)

formatter = TextFormatter()

def get_and_enhance_transcript(youtube_url):
    try:
        video_id = youtube_url.split('v=')[-1]
        transcript = None
        language = None

        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['hi'])
            language = 'hi'
        except:
            try:
                transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
                language = 'en'
            except:
                return None, None

        formatted_transcript = formatter.format_transcript(transcript)

        prompt = f"""
        Act as a transcript cleaner. Generate a new transcript with the same context and the content only covered in the given transcript. If there is a revision portion differentiate it with the actual transcript.
        Give the results in sentences line by line, not in a single line.
        Transcript: {formatted_transcript}
        """

        llm = ChatGroq(
            model="llama-3.1-70b-versatile",
            temperature=0,
            groq_api_key="I won't tell"
        )

        enhanced_transcript = llm.invoke(prompt)

        return enhanced_transcript, language
    except Exception as e:
        print(f"Error: {str(e)}")
        return None, None

def generate_summary_and_quiz(transcript, num_questions, language, difficulty):
    try:
        prompt = f"""
        Summarize the following transcript by identifying the key topics covered, and provide a detailed summary of each topic in 6-7 sentences.
        Each topic should be labeled clearly as "Topic X", where X is the topic name. Provide the full summary for each topic in English, even if the transcript is in a different language.

        After the summary, give the name of the topic on which the transcript was all about in a maximum of 2 to 3 words.
        After summarizing, create a quiz with {num_questions} multiple-choice questions in English, based on the transcript content.
        Only generate {difficulty} difficulty questions. Format the output in JSON format.

        Transcript: {transcript}
        """

        llm = ChatGroq(
            model="llama-3.1-70b-versatile",
            temperature=0,
            groq_api_key="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"
        )
        response = llm.invoke(prompt)

        if hasattr(response, 'content'):
            response_content = response.content
            try:
                response_dict = json.loads(response_content)
                return response_dict
            except json.JSONDecodeError as e:
                return None
        return None
    except Exception as e:
        return None

@app.route('/generate_quiz', methods=['POST'])
def generate_quiz():
    data = request.json
    youtube_link = data.get('youtube_url')
    num_questions = data.get('num_questions', 5)
    difficulty = data.get('difficulty', 'medium')

    if youtube_link:
        transcript, language = get_and_enhance_transcript(youtube_link)
        
        if transcript:
            summary_and_quiz = generate_summary_and_quiz(transcript, num_questions, language, difficulty)
            if summary_and_quiz:
                return jsonify(summary_and_quiz)
            else:
                return jsonify({"error": "Failed to generate quiz"}), 500
        else:
            return jsonify({"error": "Failed to fetch transcript"}), 404
    else:
        return jsonify({"error": "No YouTube URL provided"}), 400

if __name__ == '__main__':
    app.run(debug=True)
