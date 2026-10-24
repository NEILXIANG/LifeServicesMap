# Kamloops Newcomer Assistant — A Brief for Organisations

**Test version, October 2026** · https://kamloops-assistant.neilxiang.workers.dev · Prepared by Neil Xiang

## What it is

A free web page where a newcomer, or a staff member helping one, can ask an everyday settlement question in any language: school enrolment, MSP, a SIN, food, legal help. The answer is written by AI, but **only from the verified content of the Kamloops Life Guide** (17 step-by-step task cards and 387 places), and every step names its source and the month it was last checked.

It is an **independent pilot**. It is not a service of Kamloops Immigrant Services, the City of Kamloops or any government, and it says so on every page. The Life Guide itself is unchanged and separate: it stays free, works offline and collects no personal information.

## How an answer is made

1. **Crisis check first.** If a question looks like violence, self-harm or another emergency — including when someone asks on behalf of another person — the page shows 9-1-1 and 24-hour help lines straight away. **The question is not sent to the AI.**
2. **Look up the guide.** The program picks the relevant task cards and places from the guide.
3. **Write the answer.** Anthropic's Claude model writes a short answer using only that content, citing a source for every step.
4. **Check the answer.** Before anything is shown, the program checks that every cited source is real, and that every phone number and web address appears in the source it cites. A step that fails is removed; if nothing is left, the page says the guide has no verified information and refers the person to KIS and 2-1-1.

## What it will not do

- Decide anyone's eligibility, immigration status, legal position or medical situation. For those questions it gives the general process and says who can help with the person's own case.
- Invent phone numbers, addresses, fees or deadlines.
- Act on instructions hidden in a question (for example "ignore your rules").
- Replace settlement workers. It points people to them.

## Privacy

| | |
|---|---|
| **Not collected** | Names, contact details, ID numbers, immigration status, health information. The page asks people not to type them, and warns before sending if a question looks like it contains a phone number, email or ID number. |
| **Not stored** | Questions and answers are not saved anywhere, and server logs do not record questions. |
| **Sent to the AI service** | Only the question text and the relevant guide content. The service is Anthropic's Claude API; Anthropic is a US company, so questions are processed outside Canada. By default Anthropic does not train its models on API data. Crisis questions are never sent. |
| **Usage limits** | To count questions per day, the service keeps a one-way code made from the visitor's internet address and the date — not the address itself — and deletes it after two days. |
| **Feedback** | Anonymous "useful / wrong / didn't answer my question", with an optional sentence (numbers and email addresses are removed). |

Organisations that would offer it to clients may want their own privacy review (a privacy impact assessment is common practice in BC).

## Cost and limits

- About **4 US cents per answer**. Currently paid by Neil from an Anthropic API account with a prepaid balance, so spending cannot run past what has been loaded.
- **Test-version limits:** 10 questions per person per day, 5 per minute, and 200 for the whole site per day. Crisis questions are not counted.
- No cost to organisations or users.

## How it has been tested

- 74 automated checks run before every release. They use a simulated AI and deliberately try invented phone numbers, fake sources, crisis wording in six languages (first and third person), hidden instructions and translation errors, to prove each safeguard catches them.
- A bank of 30 test questions covers common processes, eligibility, crisis, questions the guide cannot answer, invented-number traps, personal details and other languages. A core set (an everyday process, an eligibility question and a hidden-instruction attempt) is re-run with the real AI after each change; the crisis questions are checked every time without the AI.
- Checked by hand in a browser on phone and desktop, in all six interface languages, including dark mode.

## Languages

The interface is in English, French, Spanish, Chinese, Korean and Japanese. Questions can be asked in any language; the answer comes back in the language of the question.

## Control

- It can be switched to **staff-only** (sign-in with a registered email) or **turned off** at any time, without affecting the Life Guide.
- When the guide's content is updated and re-checked, the assistant uses the new content after the next rebuild.

## What would help from you

1. Try 3–5 questions your staff hear most often, and tell us where an answer is wrong, unclear or missing.
2. Tell us whether it would be more useful for staff, for clients, or not at all.
3. Tell us what you would need — privacy, wording, oversight — before you would feel comfortable pointing people to it.

**Contact:** Neil Xiang — [email]
