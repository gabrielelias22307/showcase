// Optional practice: WorkKeys Workplace Documents (Levels 3-7).
//
// Turned on with the "Extra practice" switches (start screen or
// Notebook > My progress), or locked by the teacher with ?practice=docs.
// These tasks never change the mystery. Each one is handed out by a
// character in the room and comes with a short workplace document.
//
// Documents get longer and harder by level, following ACT's Workplace
// Documents level descriptions (see STANDARDS.md):
//   L3-4 short notices and procedures, L5 if-then rules and defined
//   acronyms, L6 jargon to work out from context and new situations,
//   L7 dense, unclear writing where one section must be applied to another.
//
// Document format: { kind, title, meta: [[label, value]], body: [...] }
// body items: 'a paragraph' | { h: 'heading' } | { ol: [...] } | { ul: [...] }

export default {
  id: 'docs',
  label: 'Workplace Documents',
  icon: '📄',
  taskWord: 'Reading task',
  description: 'Read memos, notices, rules and policies, then decide what to do.',

  items: {
    WD1: {
      level: 3, skill: 'Decide when to do a step',
      from: 'jordan', title: 'Hall pass rules',
      intro: 'New students always ask me how the hall pass works. Here are the rules.',
      doc: {
        kind: 'Procedure', title: 'Room 210 Hall Pass Rules',
        body: [
          { ol: [
            'Sign out: write your name, where you are going, and the time.',
            'Take the hall pass.',
            'Come back within 10 minutes.',
            'Sign in: write the time you return. Put the hall pass back.'
          ] }
        ]
      },
      prompt: 'A student needs to go to the nurse. What should the student do FIRST?',
      options: [
        { text: 'Take the hall pass', feedback: 'That is step 2. What comes before it?' },
        { text: 'Write their name, where they are going, and the time', correct: true, feedback: 'Correct. Step 1 is to sign out.' },
        { text: 'Come back within 10 minutes', feedback: 'That is step 3. Look at step 1.' },
        { text: 'Write the time they return', feedback: 'That is the last step, when the student comes back.' }
      ]
    },

    WD2: {
      level: 3, skill: 'Find the main point',
      from: 'ana', title: 'Book cart notice',
      intro: 'The library posts this notice on every cart.',
      doc: {
        kind: 'Notice', title: 'Library Book Carts',
        body: [
          'All book carts must be returned to the library by 4:00 PM every school day.',
          'Do not leave a cart in a hallway or classroom overnight.',
          'If a cart has a broken wheel, tell the front desk.'
        ]
      },
      prompt: 'What is the main point of this notice?',
      options: [
        { text: 'Students may borrow book carts after school.', feedback: 'The notice does not talk about students borrowing carts.' },
        { text: 'Students must fix broken wheels.', feedback: 'The notice says to TELL the front desk about a broken wheel, not to fix it.' },
        { text: 'Carts should be kept in the hallway.', feedback: 'The notice says the opposite: do not leave carts in a hallway.' },
        { text: 'Carts must go back to the library by 4:00 PM every school day.', correct: true, feedback: 'Correct. The rest of the notice supports this main rule.' }
      ]
    },

    WD3: {
      level: 4, skill: 'Choose an action when conditions change',
      from: 'marcus', title: 'Battery charging',
      intro: 'I also charge the camera batteries. Mr. Elias made us a procedure.',
      doc: {
        kind: 'Procedure', title: 'Camera Battery Charging',
        meta: [['From', 'Mr. Elias, Yearbook Adviser']],
        body: [
          'Charge batteries only at the charging station on Layout Table 2. Never leave a charging battery alone.',
          { ol: [
            'Check the battery for cracks, swelling or loose wires. Do not charge a damaged battery.',
            'Connect the battery to the charger, then plug the charger into the wall.',
            'Check the battery every 10 minutes while it charges.',
            'When the light turns green, unplug the charger from the wall first, then disconnect the battery.'
          ] },
          'If a battery becomes hot to the touch while charging, unplug the charger right away, place the battery in the metal safety bin, and tell the coach.'
        ]
      },
      prompt: 'Marcus is charging a battery. During a 10-minute check, the battery feels hot. What should he do?',
      options: [
        { text: 'Unplug the charger, put the battery in the metal safety bin, and tell the coach.', correct: true, feedback: 'Correct. The last paragraph says exactly what to do when a battery gets hot.' },
        { text: 'Keep charging, but check it every 5 minutes instead of every 10.', feedback: 'The procedure says to stop charging right away if the battery gets hot.' },
        { text: 'Finish charging until the light is green, then tell the coach.', feedback: 'Waiting is not safe. The procedure says to unplug it right away.' },
        { text: 'Move the battery to a student table to cool down.', feedback: 'The procedure says to use the metal safety bin.' }
      ]
    },

    WD4: {
      level: 4, skill: 'Figure out the meaning of a word from the document',
      from: 'riley', title: 'Trophy rotation',
      intro: 'This is the notice about who keeps the trophy over the summer. That\'s what the vote was about.',
      doc: {
        kind: 'Notice', title: 'Summer Trophy Rotation',
        meta: [['To', 'Yearbook staff'], ['From', 'Mr. Elias']],
        body: [
          'This summer, our Best Yearbook trophy will rotate among staff members. Each member keeps it for two weeks. The first holder was chosen by staff vote.',
          'While you have the trophy, you are its custodian. As custodian, you must keep it indoors, keep it safe from damage, and bring it to the next holder on the date on the schedule.',
          'If the trophy is damaged while you are its custodian, tell Mr. Elias the same day.'
        ]
      },
      prompt: 'In this notice, what does the word "custodian" most likely mean?',
      options: [
        { text: 'A person who cleans the school building', feedback: 'That is another meaning of the word, but it does not fit this notice. Read what a custodian must do.' },
        { text: 'The person in charge of taking care of the trophy', correct: true, feedback: 'Correct. The notice says the custodian must keep the trophy safe and pass it on.' },
        { text: 'The person who won the staff vote', feedback: 'Only the FIRST holder was chosen by vote. Every holder becomes a custodian.' },
        { text: 'The editor-in-chief', feedback: 'The notice says any staff member who has the trophy is its custodian.' }
      ]
    },

    WD5: {
      level: 5, skill: 'Apply if-then instructions and acronyms',
      from: 'grump', title: 'Shelf sensor guide',
      intro: 'The district sent me this guide for the shelf sensors. I had to read it three times. Your turn.',
      doc: {
        kind: 'User guide', title: 'Trophy Case Shelf Sensors: Quick Guide',
        body: [
          'Each shelf in the trophy case sits on a load cell (LC). An LC measures weight. Every LC sends its reading to the data logger (DL) once every 60 seconds.',
          { h: 'What the DL does' },
          { ul: [
            'If a shelf\'s weight changes by more than 0.5 kg in one minute, the DL records an EVENT with the time.',
            'If a shelf\'s weight changes by 0.5 kg or less, the DL saves the reading but does not record an event.',
            'If the battery light on the DL is red, readings may be lost. Replace the battery within 24 hours.'
          ] },
          'To print a graph, connect the DL to the classroom laptop and choose Export.'
        ]
      },
      prompt: 'The weight on Shelf 2 drops by 0.8 kg in one minute. The battery light is green. What does the DL do?',
      options: [
        { text: 'Nothing. Only drops of more than 1 kg count.', feedback: 'Check the number in the guide: the limit is 0.5 kg.' },
        { text: 'The LC turns off.', feedback: 'The guide does not say the load cell ever turns off.' },
        { text: 'It records an EVENT with the time.', correct: true, feedback: 'Correct. 0.8 kg is more than 0.5 kg, so the DL (data logger) records an event.' },
        { text: 'It turns the battery light red.', feedback: 'The battery light shows the battery level, not weight changes. The light is green.' }
      ]
    },

    WD6: {
      level: 5, skill: 'Apply a policy to a similar situation',
      from: 'ortiz', title: 'After-school room policy',
      intro: 'Here is the school\'s policy for using rooms after school. Every club advisor has to follow it.',
      doc: {
        kind: 'Policy', title: 'After-School Room Use',
        meta: [['From', 'Main Office'], ['Applies to', 'All after-school clubs']],
        body: [
          'At 3:00 PM, outside classroom doors lock automatically. Students and staff re-enter by scanning an ID badge.',
          'Students who leave the room must sign out on the hall pass log. Students who return must re-enter through the main door unless the advisor approves another door.',
          'Visitors (anyone who is not a club member or the advisor) must sign the hall pass log and wear a visitor sticker while in the room. Visitor stickers are kept at the hall pass desk.',
          'Advisors must keep the room\'s trophy and display cases locked when they are not in use.'
        ]
      },
      prompt: 'Ana is a library aide. She is not on the yearbook staff. She arrives at Room 210 at 3:15. According to the policy, what must she do?',
      options: [
        { text: 'Nothing. She works for the library, so she is not a visitor.', feedback: 'The policy defines a visitor as anyone who is not a club member or the advisor. That includes Ana.' },
        { text: 'Scan her badge at Door B, the closest door to the library.', feedback: 'The policy does not say visitors may choose any door. And it does not say Door B is closest to the library.' },
        { text: 'Sign the hall pass log and wear a visitor sticker.', correct: true, feedback: 'Correct. Ana is not a club member or the advisor, so she is a visitor.' },
        { text: 'Ask the advisor to approve a different door.', feedback: 'That rule is for students who return. Visitors must sign the log and wear a sticker.' }
      ]
    },

    WD7: {
      level: 6, skill: 'Work out a technical term and apply a rule to a new situation',
      from: 'sam', title: 'Yearbook contest rules',
      intro: 'As editor-in-chief I have to know the contest rules. This section always confuses people.',
      doc: {
        kind: 'Rule book', title: 'Section 4: Spread Entries',
        meta: [['From', 'State Yearbook Contest Rule Book, 2026']],
        body: [
          '4.1 Each entry is one spread (two facing pages) at trim size, 9 in × 12 in per page. Judges may ask for a corrected file at any time.',
          '4.2 Photos and background colors may run into the bleed, the 1/8-inch strip beyond the trim edge that is cut away after printing.',
          '4.3 All text must stay inside the safe area, at least 1/2 inch inside the trim edge. An entry with text outside the safe area may not be judged until it is corrected.',
          '4.4 Entries may not be changed after the deadline without the judges\' approval.'
        ]
      },
      prompt: 'On Sam\'s spread, a photo runs 1/8 inch past the trim edge. All of the text is 3/4 inch inside the trim edge. According to Section 4, can the spread be judged?',
      options: [
        { text: 'No, because the photo goes past the trim edge.', feedback: 'Rule 4.2 allows photos to run into the bleed past the trim edge.' },
        { text: 'No, because the judges must check every file again.', feedback: 'Rule 4.1 says judges MAY ask for a corrected file. It does not say they must.' },
        { text: 'Yes, because the size rules only apply at the state finals.', feedback: 'Section 4 does not say that. The rules apply to every entry.' },
        { text: 'Yes. The photo stays in the bleed, and the text is inside the safe area.', correct: true, feedback: 'Correct. The "bleed" is the strip that gets cut off (4.2), and 3/4 inch is more than the 1/2 inch the safe area needs (4.3).' }
      ]
    },

    WD8: {
      level: 6, skill: 'Identify the reason behind a rule',
      from: 'grump', title: 'Principal\'s memo',
      intro: 'I wrote this memo after the last fire drill. Read it. Carefully.',
      doc: {
        kind: 'Memo', title: 'Hall Pass Logs',
        meta: [['To', 'All teachers and club advisors'], ['From', 'Principal Grump'], ['Re', 'Changes to hall pass logs']],
        body: [
          'Effective Monday, every classroom hall pass log must record both the time a student leaves and the time the student returns.',
          'During last month\'s fire drill, several rooms could not confirm within five minutes which students were present. Their logs showed when students left, but not whether they had returned. Staff had to search hallways and restrooms room by room.',
          'Please make sure the "Time in" column is completed every time a student comes back. Logs will be checked during the next drill.'
        ]
      },
      prompt: 'What is the main reason the principal requires a "Time in" column?',
      options: [
        { text: 'So that in an emergency, staff can quickly tell which students are in the room.', correct: true, feedback: 'Correct. The memo explains that during the drill, rooms could not confirm who was present because the logs had no return times.' },
        { text: 'So that teachers can grade students on how fast they return.', feedback: 'The memo never mentions grades.' },
        { text: 'So that students spend less time in the hallways.', feedback: 'That might happen, but the memo gives a different reason. Re-read the second paragraph.' },
        { text: 'Because the logs will be checked during the next drill.', feedback: 'That is how the rule will be checked, not why the rule exists.' }
      ]
    },

    WD9: {
      level: 7, skill: 'Apply one section of a document to another',
      from: 'marcus', title: 'Key control procedure',
      intro: 'Mr. Elias gave me the official key procedure when I became photo editor. It is very hard to read.',
      doc: {
        kind: 'Procedure', title: 'Equipment Custody and Key Control (Rev. 3)',
        meta: [['Issued by', 'Facilities Office'], ['Scope', 'Secured storage units: display cases, camera cabinets, equipment lockers']],
        body: [
          { h: '2. Issuance' },
          '2.1 Keys to secured storage units shall be issued exclusively to persons enumerated on the authorized roster maintained by the supervising faculty member.',
          { h: '3. Access' },
          '3.2 The key holder of record shall remain physically present at the unit for the duration of access.',
          '3.4 Upon completion of access, the key holder of record shall restore the unit to its secured state prior to relinquishing the key. Failure to do so shall constitute a breach, notwithstanding the timely return of the key.',
          { h: '5. Reporting' },
          '5.1 Any breach, whether or not loss or damage results, shall be reported to the supervising faculty member no later than the end of the following school day.'
        ]
      },
      prompt: 'A staff member uses the key to get a camera from the camera cabinet. She returns the key on time, but she leaves the cabinet unlocked. Nothing is missing. Using Sections 3.4 and 5.1, what is true?',
      options: [
        { text: 'There was no breach, because the key was returned on time.', feedback: 'Section 3.4 says it is a breach "notwithstanding" (even if) the key was returned on time.' },
        { text: 'It was a breach, and it must be reported to the supervising teacher by the end of the next school day.', correct: true, feedback: 'Correct. Not locking the unit is a breach (3.4), and every breach must be reported, even with no loss (5.1).' },
        { text: 'It was a breach, but it only needs to be reported if something is missing.', feedback: 'Section 5.1 says "whether or not loss or damage results." It must be reported either way.' },
        { text: 'Only the Facilities Office can decide if it was a breach.', feedback: 'Section 3.4 already defines the breach. Section 5.1 says who to report it to.' }
      ]
    },

    WD10: {
      level: 7, skill: 'Infer implied details and draw a conclusion',
      from: 'ana', title: 'Equipment loan agreement',
      intro: 'Priya borrowed a camera kit from the library. Here is the loan agreement she signed.',
      doc: {
        kind: 'Agreement', title: 'Library Equipment Loan Agreement',
        meta: [['Borrower', 'Priya S.'], ['Item', 'Camera kit #4'], ['Loan period', '14 days']],
        body: [
          'The borrower assumes responsibility for the item from checkout until check-in, exclusive of normal wear.',
          'Items not checked in by the end of the loan period accrue a fee of $1.00 per school day, not to exceed the replacement cost of the item.',
          'One renewal of the loan period may be requested at the front desk on or before the due date, provided no other patron has placed a hold on the item.',
          'Items with a hold may not be renewed and must be checked in by the due date so they can be issued to the next patron.'
        ]
      },
      prompt: 'Priya\'s loan ends today. Another student has placed a hold on the camera kit. What should Priya do?',
      options: [
        { text: 'Renew the loan at the front desk today.', feedback: 'Renewals are allowed only if no one has placed a hold. Someone has.' },
        { text: 'Keep it and pay $1.00 per school day for as long as she needs it.', feedback: 'The agreement says the kit must be checked in by the due date when there is a hold. Also, the fee is capped at the replacement cost.' },
        { text: 'Keep it one more week, because there is no fee for the first week.', feedback: 'The agreement says fees start right after the loan period ends.' },
        { text: 'Check the kit in today, because items with a hold cannot be renewed.', correct: true, feedback: 'Correct. Because another patron (library user) placed a hold, Priya cannot renew and must return the kit by today.' }
      ]
    }
  }
};
