# Prompt for GPT to Generate Training Meeting Transcript

Copy and paste this prompt into GPT-4 or GPT-5.1 to generate a realistic training meeting transcript for testing:

---

**PROMPT:**

Generate a realistic 1-hour training meeting transcript (approximately 8,000-10,000 words) for a corporate training session on "Azure AI Services for Document Processing". 

**Requirements:**

1. **Meeting Context:**
   - Training session for software developers and DevOps engineers
   - Instructor-led with Q&A sessions
   - 3-4 participants asking questions throughout
   - Include timestamps every 2-3 minutes
   - Professional but conversational tone

2. **Content Coverage:**
   - Introduction to Azure Document Intelligence (5 min)
   - Key features and capabilities (10 min)
   - Architecture and integration patterns (15 min)
   - Hands-on demo walkthrough (20 min)
   - Best practices and common pitfalls (7 min)
   - Q&A session (3 min)

3. **Reference URLs to Include:**
   Throughout the transcript, the instructor should naturally reference these URLs (mention them verbally as resources):
   
   - https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/overview
   - https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/quickstarts/get-started-sdks-rest-api
   - https://learn.microsoft.com/en-us/azure/architecture/ai-ml/architecture/automate-document-processing-azure-form-recognizer
   - https://docs.python.org/3/library/asyncio.html
   - https://fastapi.tiangolo.com/tutorial/background-tasks/
   - https://learn.microsoft.com/en-us/azure/cosmos-db/introduction
   - https://learn.microsoft.com/en-us/azure/storage/blobs/storage-blobs-overview

4. **Transcript Format:**
   ```
   [00:00:00] Instructor (Sarah Chen): Good morning everyone! Welcome to today's training session...
   
   [00:02:15] Instructor: Let me share my screen. As you can see on the Microsoft documentation at...
   
   [00:15:30] Participant (Mike Rodriguez): Quick question about the pricing model...
   ```

5. **Realistic Elements Include:**
   - Technical jargon and acronyms
   - Occasional stumbles or corrections ("Actually, let me rephrase that...")
   - Screen sharing references
   - Code snippet discussions
   - Practical examples and use cases
   - Troubleshooting tips
   - Performance optimization advice

6. **At the End, Provide:**
   A separate list of all URLs mentioned in the transcript in this format:
   ```
   **Referenced URLs for Knowledge Sources:**
   - https://learn.microsoft.com/...
   - https://learn.microsoft.com/...
   ```

**Output the complete transcript below:**

---

## How to Use This Generated Content

1. Copy the prompt above into ChatGPT (GPT-4 or GPT-5.1)
2. Save the generated transcript as `training_azure_ai_services.txt` in the `sample_data/transcripts/` folder
3. Extract the list of URLs from the end of the transcript
4. Test your app by:
   - Uploading the transcript file
   - Pasting the URL list into the `knowledge_urls` parameter
   - Verifying that the generated documentation includes content from both the transcript and the referenced URLs

## Expected Output

The generated transcript should be:
- **Length:** 8,000-10,000 words (approximately 1 hour of speech at 140-160 words/minute)
- **Format:** Plain text with timestamps
- **URLs:** 7+ reference URLs naturally mentioned throughout
- **Quality:** Professional, educational, realistic conversation flow
- **Topics:** Technical depth appropriate for software developers

This will thoroughly test your document generation pipeline's ability to:
- Process long-form transcripts
- Fetch and integrate content from multiple knowledge URLs
- Generate structured documentation from conversational content
- Handle technical terminology and code references
