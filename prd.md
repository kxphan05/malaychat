# One-pager: MalayChat - Free Local Malay Language Learning App

## 1. TL;DR
MalayChat is a free, locally-run language learning application that helps non-Malay speakers learn conversational Malay through AI-powered chat interactions. Built on the mesolitica/mallam-3B-4096 model and delivered through a Streamlit interface, it fills the gap left by major platforms like Duolingo that don't offer Malay language instruction. By running inference locally via HuggingFace, users get unlimited practice without subscription fees or internet dependency.

## 2. Goals

### Business Goals
* Establish the first free, accessible Malay language learning tool that runs entirely on local hardware
* Build a user base of 10,000+ active learners within the first year
* Demonstrate viability of locally-run language learning models as an alternative to cloud-based subscription services
* Create a community-driven feedback loop to improve Malay language instruction quality

### User Goals
* Learn practical Malay vocabulary and phrases for everyday situations without paying subscription fees
* Practice conversational Malay in a low-pressure environment with immediate feedback
* Set and track personalized learning objectives based on real-world needs
* Access language learning tools offline or with minimal internet connectivity

### Non-Goals
* Competing with comprehensive language certification programs
* Supporting languages beyond Malay in the initial release
* Building native mobile apps (web-based Streamlit interface only)
* Providing formal grammar instruction or structured curriculum paths
* Monetization through premium tiers or advertisements

## 3. User stories

**Primary Persona: Alex - The Expatriate Professional**
* As an expat working in Malaysia, I want to learn marketplace vocabulary so I can shop at local markets confidently
* As a professional relocating to Malaysia, I want to practice basic conversational phrases so I can build relationships with colleagues

**Secondary Persona: Maya - The Heritage Language Learner**
* As someone with Malay heritage, I want to reconnect with my family's language so I can communicate with older relatives
* As a heritage learner, I want flexible practice sessions so I can learn at my own pace around my schedule

**Tertiary Persona: Jordan - The Budget-Conscious Student**
* As a linguistics student, I want to explore Southeast Asian languages without subscription costs so I can expand my knowledge affordably
* As a traveler preparing for a trip, I want to learn survival phrases so I can navigate Malaysia independently

## 4. Functional requirements

### P0 - Must Have (MVP)
* **Local Model Integration**: HuggingFace integration to run mesolitica/mallam-3B-4096 model locally for inference
* **Dual-Mode Interface**: Toggle between Learning Mode (structured practice) and Chat Mode (freeform conversation)
* **Session Goal System**: Sidebar panel where users can manually add learning goals for the current session
* **Goal Completion Tracking**: Automatic detection and marking of completed goals during conversation
* **Streamlit Chat Interface**: Clean, responsive chat UI with message history and mode indicators
* **Basic Conversation Flow**: Text input/output with the Malay language model, maintaining context within sessions

### P1 - Should Have (v1.1)
* **Auto-Goal Suggestions**: System-generated goal recommendations based on conversation context and common learning patterns
* **Session History**: Save and review past conversations and completed goals
* **Progress Dashboard**: Visual representation of goals completed over time
* **Vocabulary Highlighting**: Automatic identification and emphasis of new words learned during sessions
* **Example Phrases Library**: Quick-access common phrases organized by scenarios (marketplace, greetings, dining, etc.)

### P2 - Nice to Have (Future)
* **Pronunciation Guide**: Romanization and phonetic spelling for Malay words
* **Difficulty Adjustment**: Adaptive conversation complexity based on user proficiency
* **Export Functionality**: Download conversation transcripts and vocabulary lists
* **Themed Learning Paths**: Pre-built goal sets for specific scenarios (travel, business, social)
* **Community Contributions**: User-submitted goal templates and practice scenarios

## 5. User experience

### Happy Path User Journey
* User launches the Streamlit app and sees a clean chat interface with a welcome message
* User selects "Learning Mode" from the mode toggle at the top
* User adds a goal in the sidebar: "Learn 3 words to use in the marketplace"
* System acknowledges the goal and suggests starting with common marketplace items
* User engages in conversation, asking "How do I ask for the price?"
* Bot responds with the phrase and uses it in context
* User practices the phrase several times in different scenarios
* System automatically detects the user has learned 3 marketplace words and marks the goal complete with a checkmark
* User switches to "Chat Mode" to practice freestyle conversation using newly learned vocabulary

### Edge Cases & UI Notes
* **First-time setup**: Display clear instructions for downloading the model if not already cached locally
* **Model loading time**: Show progress indicator during initial model load (may take 30-60 seconds)
* **Incomplete goals**: Allow users to delete or edit goals mid-session without penalty
* **Mode switching**: Preserve conversation context when switching between Learning and Chat modes
* **Session persistence**: Warn users before closing if they have active goals that haven't been saved
* **Error handling**: Graceful fallback messages if model inference fails, with option to retry
* **Empty state**: Provide starter prompts when goal sidebar is empty ("Try adding: Learn greetings" or "Learn to order food")
* **Long conversations**: Implement smart context truncation to maintain performance after extended sessions

## 6. Narrative

It's 6:30 AM in Kuala Lumpur. Sarah, a marketing consultant who moved from Singapore three months ago, opens her laptop while having breakfast. She's heading to Pasar Seni later and wants to finally stop relying on English at the local market.

She launches MalayChat and immediately adds a goal: "Learn to negotiate prices at the market." The interface is familiar and uncluttered—just a chat window and her goals listed neatly in the sidebar.

"Hi! I'm going to the market today. How do I ask for the price?" she types.

The bot responds warmly in a mix of English and Malay: "Great! You'd say 'Berapa harga ini?' (How much is this?). Let's practice using it!"

They go back and forth. The bot plays different roles—a fruit vendor, a textile seller—each time weaving in the vocabulary naturally. Sarah asks about bargaining phrases. The bot teaches her "Boleh kurang sikit?" (Can you reduce a little?) and uses it in realistic scenarios.

Twenty minutes pass. Sarah has practiced prices, bargaining, and learned to say "Terima kasih, saya ambil ini" (Thank you, I'll take this). She notices the checkmark appear next to her goal in the sidebar—she's learned the vocabulary she needed.

She switches to Chat Mode and has a freeform conversation about her weekend plans, naturally incorporating what she just learned. No pressure, no timers, no paywall blocking her progress.

At the market four hours later, when the aunty asks "Nak berapa biji?" (How many do you want?), Sarah understands and responds confidently. The connection she feels in that moment—small but significant—started with a free tool on her laptop that morning.

## 7. Success metrics

### Primary Metrics
* **Active Users**: Number of users completing at least one learning session per week
* **Goals Completed**: Average number of goals completed per user session (target: 2-3)
* **Session Duration**: Average time spent in Learning Mode per session (target: 15-25 minutes)
* **Return Rate**: Percentage of users who return for a second session within 7 days (target: 40%+)

### Secondary Metrics
* **Mode Usage Split**: Ratio of time spent in Learning Mode vs Chat Mode
* **Goal Creation Rate**: Percentage of sessions where users create custom goals (vs. accepting suggestions)
* **Conversation Length**: Average number of messages exchanged per session
* **Model Performance**: Inference speed and response quality ratings (user feedback)

### Learning Outcome Metrics
* **Vocabulary Retention**: Number of unique words/phrases practiced across sessions
* **Goal Diversity**: Variety of learning topics users explore (marketplace, greetings, social, etc.)
* **User Self-Assessment**: Quarterly survey on confidence speaking basic Malay

## 8. Milestones & sequencing

### Phase 1: MVP Foundation (Weeks 1-4)
* Week 1-2: Set up HuggingFace integration, test mesolitica/mallam-3B-4096 model locally
* Week 3: Build basic Streamlit chat interface with mode toggle
* Week 4: Implement goal sidebar with manual entry and completion tracking
* **Deliverable**: Working prototype for internal testing

### Phase 2: Core Experience (Weeks 5-8)
* Week 5: Refine conversation quality and context handling
* Week 6: Add auto-goal suggestion system based on conversation patterns
* Week 7: Implement session history and basic progress tracking
* Week 8: Polish UI/UX, add error handling and edge case management
* **Deliverable**: Beta release to 50 test users

### Phase 3: Launch & Iterate (Weeks 9-12)
* Week 9: Incorporate beta feedback, optimize model performance
* Week 10: Add vocabulary highlighting and example phrases library
* Week 11: Build onboarding flow and first-time user experience
* Week 12: Public launch with documentation and community feedback channels
* **Deliverable**: Public v1.0 release

### Phase 4: Growth & Enhancement (Months 4-6)
* Add progress dashboard and learning analytics
* Implement themed learning paths and community-contributed scenarios
* Optimize for lower-spec hardware to improve accessibility
* Build feedback loop for continuous model and content improvements
* **Deliverable**: Enhanced v1.1 with community features 