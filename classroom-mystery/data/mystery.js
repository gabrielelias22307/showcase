// The Case of the Missing Robotics Trophy
//
// Every clue is a workplace-style graphic. Each graphic comes with one
// question written to a WorkKeys Graphic Literacy level (3-7). Answering it
// turns the graphic into a "fact" in the notebook. The final case review
// asks the higher-level questions (L6-L7) that combine two graphics.
//
// World coordinates (meters): x runs west (-12) to east (+12),
// z runs north (-8) to south (+8). The floor-plan graphic is drawn from the
// same room.objects list, so the 3D room and the map always agree.

export default {
  id: 'robotics-trophy-v1',
  title: 'The Case of the Missing Robotics Trophy',
  setting: 'Room 210, 3:55 PM, after school',

  intro: [
    'Room 210 is the biggest classroom in the building. It has its own computer lab and a small office. The robotics club meets here after school.',
    'At 3:50 PM, Ms. Ortiz noticed that the state championship trophy was gone from the trophy case.',
    'You just got here. Everyone who was in the room is still here. Talk to them, collect their charts, logs and maps, and read each graphic carefully.',
    'When you have the facts, tell Ms. Ortiz what happened.'
  ],

  controls: 'Move: W A S D or arrow keys. Look: drag with the mouse. Talk or examine: E (or click the button). Notebook: N.',

  // Spawn just inside Door A, looking east at the hall pass desk.
  player: { spawn: [-11.0, 6.0], yaw: -Math.PI / 2 },

  // Laid out from photos of the real room: a classroom (south), with a
  // computer lab and a small office behind a wall with two openings.
  room: {
    width: 24,
    depth: 16,
    height: 3.4,
    // Outside doors. at = x on the north/south walls, z on the east/west walls.
    doors: [
      { id: 'doorA', label: 'Door A (Main)', wall: 'west', at: 6, width: 1.2 },
      { id: 'doorB', label: 'Door B (Lab)', wall: 'north', at: -9, width: 1.2 }
    ],
    // Inside walls. Openings are doorways you can walk through.
    walls: [
      { id: 'labWall', from: [-12, -2], to: [12, -2], openings: [{ at: 3.5, width: 1.4 }, { at: 8.8, width: 1.0 }] },
      { id: 'officeWall', from: [7, -8], to: [7, -2], openings: [] }
    ],
    // Room names on the floor plan
    areas: [
      { label: 'Classroom', x: 8.3, z: 5.2 },
      { label: 'Computer lab', x: -4.6, z: -6.3 },
      { label: 'Office', x: 9.3, z: -3.4 }
    ],
    // The classroom's east wall is painted blue, like the real room.
    paint: [{ wall: 'east', from: -2, to: 8 }],
    // Paper pennant banners: { from, to, side } (side = which way the room is)
    bunting: [
      { from: [-12, 8], to: [12, 8], side: -1 },
      { from: [-12, -1.925], to: [12, -1.925], side: 1 },
      { from: [-12, -2], to: [-12, 8], side: 1 },
      { from: [12, -2], to: [12, 8], side: -1 },
      { from: [-12, -8], to: [7, -8], side: 1 },
      { from: [-12, -2.075], to: [6.925, -2.075], side: -1 },
      { from: [-12, -8], to: [-12, -2], side: 1 },
      { from: [6.925, -8], to: [6.925, -2.075], side: -1 }
    ],
    // type: table | desk | board | counter | tallcab | tv | computers | filing |
    //       bookshelf | easel | sink | sign | case | bench | cabinet | cart
    // face: which way the front of the object points (default south)
    objects: [
      // ----- Classroom -----
      { id: 'tallCabinet', label: '', type: 'tallcab', x: -11.45, z: -1.55, w: 1.0, d: 0.7, h: 2.2, plan: false, collide: true },
      { id: 'teacherDesk', label: "Teacher's desk", type: 'desk', x: -8.6, z: -0.95, w: 2.0, d: 0.8, h: 0.76, plan: true, collide: true },
      { id: 'tv', label: 'TV', type: 'tv', x: -5.4, z: -1.6, w: 1.7, d: 0.5, h: 1.9, plan: true, collide: true },
      { id: 'sign', label: '', type: 'sign', text: 'ROBOTICS', x: -5.4, z: -1.9, w: 2.4, d: 0.05, h: 0.35, y: 2.65, plan: false },
      { id: 'whiteboard', label: 'Whiteboard', type: 'board', x: -1.2, z: -1.9, w: 3.4, d: 0.1, h: 1.2, y: 1.0, plan: true },
      { id: 'westBoard', label: 'Whiteboard', type: 'board', face: 'east', x: -11.94, z: 1.4, w: 0.1, d: 4.0, h: 1.2, y: 1.0, plan: true },
      { id: 'drawers', label: '', type: 'counter', face: 'east', x: -11.65, z: 4.25, w: 0.6, d: 1.1, h: 0.9, plan: false, collide: true },
      { id: 'hallPassDesk', label: 'Hall pass desk', type: 'desk', face: 'west', x: -9.4, z: 6, w: 0.8, d: 1.6, h: 0.76, plan: true, collide: true },
      { id: 'plantCounter', label: 'Counter with plants', type: 'counter', face: 'west', uppers: true, plants: [-3.1, -2.4, -1.7, -1.0], x: 11.62, z: 3.6, w: 0.75, d: 7.0, h: 0.9, plan: true, collide: true },
      { id: 'bookshelf', label: '', type: 'bookshelf', face: 'north', x: 11.1, z: 7.65, w: 1.0, d: 0.35, h: 1.8, plan: false, collide: true },
      { id: 'bookCart', label: 'Library book cart', type: 'cart', x: 6.5, z: 7.3, w: 1.2, d: 0.6, h: 1, plan: false, collide: true },
      // Student tables: 4 columns x 3 rows, chairs on the south side
      ...[-6, -2.5, 1, 4.5].flatMap((x, ci) => [0.6, 3.2, 5.8].map((z, ri) => ({
        id: `table${ci}${ri}`, label: ri === 0 && ci === 0 ? 'Student tables' : '', type: 'table',
        x, z, w: 2, d: 0.8, h: 0.75, plan: true, collide: true
      }))),
      // ----- Computer lab -----
      { id: 'trophyCase', label: 'Trophy case', type: 'case', x: -6.8, z: -7.55, w: 2.2, d: 0.8, h: 1.9, plan: true, collide: true },
      { id: 'computers', label: 'Computers', type: 'computers', x: 2.6, z: -7.55, w: 6.8, d: 0.8, h: 0.75, plan: true, collide: true },
      { id: 'labBench1', label: 'Robotics bench', type: 'bench', x: -2.4, z: -4.6, w: 3.2, d: 1.1, h: 0.9, plan: true, collide: true },
      { id: 'labBench2', label: 'Robotics bench', type: 'bench', x: 2.6, z: -4.6, w: 3.2, d: 1.1, h: 0.9, plan: true, collide: true },
      { id: 'cabinet', label: 'Parts cabinet', type: 'cabinet', face: 'west', x: 6.55, z: -6.3, w: 0.7, d: 1.6, h: 2, plan: true, collide: true },
      { id: 'easel', label: '', type: 'easel', face: 'east', x: -10.4, z: -4.6, w: 0.6, d: 1.8, h: 2.1, plan: false, collide: true },
      { id: 'sink', label: '', type: 'sink', face: 'east', x: -11.65, z: -6.6, w: 0.7, d: 1.4, h: 0.9, plan: false, collide: true },
      // ----- Office -----
      { id: 'officeDesk', label: 'Desk', type: 'desk', x: 10.4, z: -7.25, w: 1.5, d: 0.7, h: 0.76, plan: true, collide: true },
      { id: 'filing1', label: '', type: 'filing', face: 'west', x: 11.7, z: -5.3, w: 0.6, d: 0.5, h: 1.35, plan: false, collide: true },
      { id: 'filing2', label: '', type: 'filing', face: 'west', x: 11.7, z: -4.7, w: 0.6, d: 0.5, h: 1.35, plan: false, collide: true }
    ]
  },

  npcs: [
    {
      id: 'ortiz', name: 'Ms. Ortiz', role: 'Robotics coach (teacher)', color: '#3d6fb4',
      position: [-8.6, 0.2], yaw: 0,
      dialogue: {
        start: 'root',
        nodes: {
          root: {
            text: "Thank you for coming. The trophy was in the case at 2:45. We took a team photo with it. At 3:50 it was gone. Nobody has left the room since then.",
            choices: [
              { text: 'Is there a map of the room?', next: 'map', requiresNot: ['has:E1'] },
              { text: 'Do the doors keep a record?', next: 'doors', requiresNot: ['has:E4'] },
              { text: 'Who had the key to the trophy case?', next: 'key' },
              { text: 'I think I know what happened.', next: 'ready', requires: ['ready'] },
              { text: 'I need more facts first.', next: 'notReady', requiresNot: ['ready'] },
              { text: 'Goodbye.', end: true }
            ]
          },
          map: { text: "There is a fire exit floor plan on the wall next to Door A. Go and look at it.", choices: [{ text: 'OK.', next: 'root' }] },
          doors: {
            text: "Yes. After 3:00 the doors lock from the outside. You need a badge to come in. Here is the badge chart from my laptop. It counts every badge swipe.",
            choices: [{ text: 'Thanks.', next: 'root', give: 'E4' }]
          },
          key: {
            text: "Marcus signed out the key at 3:00. He needed a ribbon from the case for our display. Ask him about the checklist.",
            choices: [{ text: 'OK.', next: 'root' }]
          },
          notReady: {
            text: "Take your time. Read every graphic in your notebook. When all your clue questions are answered, come back to me.",
            choices: [{ text: 'OK.', next: 'root' }]
          },
          ready: { text: 'Show me. Walk me through the evidence.', choices: [{ text: 'Start the case review.', action: 'accuse', end: true }] }
        }
      }
    },
    {
      id: 'jordan', name: 'Jordan', role: 'Hall pass monitor', color: '#c46a2b',
      position: [-8.6, 6], yaw: -Math.PI / 2,
      dialogue: {
        start: 'root',
        nodes: {
          root: {
            text: "I sit at the hall pass desk. Everyone who leaves the room signs out, and signs back in when they return.",
            choices: [
              { text: 'Can I see the hall pass log?', next: 'log', requiresNot: ['has:E2'] },
              { text: 'Did you see anyone near the trophy case?', next: 'case' },
              { text: 'Goodbye.', end: true }
            ]
          },
          log: { text: 'Sure. Here it is. Read the times carefully.', choices: [{ text: 'Thanks.', next: 'root', give: 'E2' }] },
          case: {
            text: "No. My desk faces Door A. The trophy case is in the computer lab, behind the wall. I can't see it from here.",
            choices: [{ text: 'OK.', next: 'root' }]
          }
        }
      }
    },
    {
      id: 'marcus', name: 'Marcus', role: 'Lab assistant', color: '#2f8a5b',
      position: [-2.4, -3.5], yaw: 0,
      dialogue: {
        start: 'root',
        nodes: {
          root: {
            text: "I didn't take the trophy! I only took a blue ribbon out of the case. I followed the key checklist.",
            choices: [
              { text: 'Can I see the checklist?', next: 'list', requiresNot: ['has:E3'] },
              { text: 'When did you use the key?', next: 'when' },
              { text: 'You skipped a step on the checklist.', next: 'skipped', requires: ['solved:E3'] },
              { text: 'Goodbye.', end: true }
            ]
          },
          list: { text: "Here. Ms. Ortiz makes us check off every step.", choices: [{ text: 'Thanks.', next: 'root', give: 'E3' }] },
          when: {
            text: "I got the key at 3:00. I opened the case around 3:18, took the ribbon, and gave the key back at 3:20. Then at 3:40 I went to the office.",
            choices: [{ text: 'OK.', next: 'root' }]
          },
          skipped: {
            text: "Oh no. I forgot to lock it. The case was unlocked after 3:20. Anyone could open it. But I promise I didn't take the trophy.",
            choices: [{ text: 'Thank you for being honest.', next: 'root', set: ['marcusAdmits'] }]
          }
        }
      }
    },
    {
      id: 'priya', name: 'Priya', role: 'Programmer, robotics club', color: '#8a3fa0',
      position: [10.3, 1.4], yaw: Math.PI / 2,
      dialogue: {
        start: 'root',
        nodes: {
          root: {
            text: "I was watering the plants on the counter. I saw the trophy in the case at about 3:25, when I went into the lab to print. It was there. I'm sure.",
            choices: [
              { text: 'Does the trophy case have any sensors?', next: 'sensor', requiresNot: ['has:E5'] },
              { text: 'Did you see anyone take it?', next: 'see' },
              { text: 'Goodbye.', end: true }
            ]
          },
          sensor: {
            text: "Yes! Our team built weight sensors for the shelves. They record the weight every minute. Here is the graph from today.",
            choices: [{ text: 'Great, thanks.', next: 'root', give: 'E5' }]
          },
          see: {
            text: "No. After 3:25 I came back to the plants. They are on the blue wall, here in the classroom. The trophy case is in the computer lab, on the other side of the wall.",
            choices: [{ text: 'OK.', next: 'root' }]
          }
        }
      }
    },
    {
      id: 'riley', name: 'Riley', role: 'Robotics club member', color: '#b23a48',
      position: [-0.75, 2], yaw: Math.PI,
      dialogue: {
        start: 'root',
        nodes: {
          root: {
            text: "Everybody is looking at me. Just because I was mad about the vote!",
            choices: [
              { text: 'What vote?', next: 'vote', requiresNot: ['has:E7'] },
              { text: 'Where were you after 3:00?', next: 'where' },
              { text: 'Goodbye.', end: true }
            ]
          },
          vote: {
            text: "The team voted on who keeps the trophy over the summer. I wanted it. Here are the results. Yes, I'm upset. But I didn't take it.",
            choices: [{ text: 'Thanks.', next: 'root', give: 'E7' }]
          },
          where: {
            text: "I went to the restroom after 3:00 and came back through Door A. Ask Jordan. After that I sat right here at this table.",
            choices: [{ text: 'OK.', next: 'root' }]
          }
        }
      }
    },
    {
      id: 'sam', name: 'Sam', role: 'Team captain', color: '#d19a1f',
      position: [5.6, -4.6], yaw: -Math.PI / 2,
      dialogue: {
        start: 'root',
        nodes: {
          root: {
            text: "Hi. I wasn't even here when it happened. I was at the library working on our team poster.",
            choices: [
              { text: 'How long were you at the library?', next: 'library' },
              { text: 'Which door did you use to come back?', next: 'door' },
              { text: "The library chart doesn't show you checking in.", next: 'confront1', requires: ['solved:E6'] },
              { text: 'Someone badged in through Door B at that time.', next: 'confront2', requires: ['solved:E4', 'solved:E6'] },
              { text: 'Goodbye.', end: true }
            ]
          },
          library: { text: 'The whole time. From 3:10 until I came back at 3:40.', choices: [{ text: 'OK.', next: 'root' }] },
          door: { text: 'Door A, the main door. Like everybody.', choices: [{ text: 'OK.', next: 'root' }] },
          confront1: {
            text: "Maybe I... forgot to check in. People forget sometimes.",
            choices: [{ text: 'OK.', next: 'root', set: ['samNervous'] }]
          },
          confront2: {
            text: "...I think I should explain this to Ms. Ortiz. Not here.",
            choices: [{ text: 'OK.', next: 'root', set: ['samNervous'] }]
          }
        }
      }
    },
    {
      id: 'ana', name: 'Ana', role: 'Library aide (visiting)', color: '#2b8f9a',
      position: [6.5, 6.4], yaw: Math.PI,
      dialogue: {
        start: 'root',
        nodes: {
          root: {
            text: "I'm just returning books for the library. I heard about the trophy. That's terrible.",
            choices: [
              { text: 'Do students check in at the library?', next: 'checkin', requiresNot: ['has:E6'] },
              { text: 'Did you see Sam at the library today?', next: 'sam' },
              { text: 'Goodbye.', end: true }
            ]
          },
          checkin: {
            text: "Yes. Every student scans their ID at the front desk. The computer makes this chart of check-ins every 10 minutes. I printed today's.",
            choices: [{ text: 'Thanks.', next: 'root', give: 'E6' }]
          },
          sam: { text: "I left the library at 3:00, so I don't know. Look at the check-in chart.", choices: [{ text: 'OK.', next: 'root' }] }
        }
      }
    }
  ],

  props: [
    {
      id: 'floorPlanPoster', name: 'Fire exit floor plan', prompt: 'Read the floor plan',
      position: [-7.5, 7.9], wall: 'south', poster: 'E1',
      examine: { text: 'A fire exit floor plan of Room 210 is posted on the wall.', give: 'E1' }
    },
    {
      id: 'trophyCaseProp', name: 'Trophy case', prompt: 'Examine the trophy case',
      position: [-6.8, -6.8],
      examine: {
        text: 'The glass door is closed but NOT locked. The top shelf (Shelf 1) is empty. There is a small sensor pad under it. The middle shelf (Shelf 2) has ribbons and medals.',
        set: ['sawCase']
      }
    }
  ],

  // Each evidence item = one graphic + one leveled question.
  evidence: {
    E1: {
      title: 'Fire Exit Floor Plan, Room 210',
      from: 'Wall poster by Door A',
      type: 'floorplan',
      level: 3,
      skill: 'Locate information in a simple graphic',
      alt: 'Floor plan of Room 210. The classroom is the south part. Door A (Main) is on its west wall, next to the hall pass desk. A wall with two openings leads north to the computer lab and a small office. The trophy case is in the computer lab, on the north wall, right next to Door B (Lab). The counter with plants is on the east wall of the classroom.',
      data: { useRoom: true, highlight: [] },
      question: {
        prompt: 'Look at the floor plan. Which door is closest to the trophy case?',
        options: [
          { text: 'Door A (Main)', feedback: 'Door A is on the west wall of the classroom, by the hall pass desk. Find the trophy case first, then look for the nearest door.' },
          { text: 'Door B (Lab)', correct: true, feedback: 'Correct. The trophy case is in the computer lab, right next to Door B.' },
          { text: 'The office doorway', feedback: 'The office is on the far east side of the plan, far from the trophy case.' },
          { text: 'There is no door near the case', feedback: 'Look again at the north wall of the computer lab.' }
        ]
      },
      fact: 'The trophy case is in the computer lab, right next to Door B (the lab door).'
    },

    E2: {
      title: 'Hall Pass Log, Room 210',
      from: 'Jordan',
      type: 'table',
      level: 3,
      skill: 'Locate information in a table',
      alt: 'Hall pass log with four rows. Priya: Nurse, out 2:30, in 2:40. Riley: Restroom, out 3:05, in 3:20. Sam: Library, out 3:10, in 3:40. Marcus: Main office, out 3:40, in 3:50.',
      data: {
        columns: ['Name', 'Destination', 'Time out', 'Time in'],
        rows: [
          ['Priya', 'Nurse', '2:30', '2:40'],
          ['Riley', 'Restroom', '3:05', '3:20'],
          ['Sam', 'Library', '3:10', '3:40'],
          ['Marcus', 'Main office', '3:40', '3:50']
        ]
      },
      question: {
        prompt: 'According to the log, where did Sam go, and how long was Sam signed out?',
        options: [
          { text: 'Restroom, 15 minutes', feedback: 'That is Riley\'s row. Find Sam\'s row first.' },
          { text: 'Library, 30 minutes', correct: true, feedback: 'Correct. Sam signed out at 3:10 and back in at 3:40. That is 30 minutes.' },
          { text: 'Library, 40 minutes', feedback: 'Subtract: 3:40 minus 3:10. Check your math.' },
          { text: 'Main office, 10 minutes', feedback: 'That is Marcus\'s row.' }
        ]
      },
      fact: 'Sam was signed out to the library from 3:10 to 3:40. Riley was back by 3:20. Marcus left at 3:40.'
    },

    E3: {
      title: 'Trophy Case Key Checklist (Marcus)',
      from: 'Marcus',
      type: 'flowchart',
      level: 5,
      skill: 'Identify the missing step in a process',
      alt: 'Flowchart with 7 steps. Marcus checked steps 1, 2, 3, 4, 6 and 7. Step 5 is blank and not checked. Steps: 1 Ask Ms. Ortiz. 2 Sign the key log. 3 Unlock the case. 4 Remove or replace the item. 5 blank. 6 Return the key. 7 Ms. Ortiz initials the log.',
      data: {
        steps: [
          { text: 'Ask Ms. Ortiz', done: true, time: '3:00' },
          { text: 'Sign the key log', done: true, time: '3:00' },
          { text: 'Unlock the case', done: true, time: '3:18' },
          { text: 'Remove or replace the item', done: true, time: '3:18' },
          { text: '?', done: false, missing: true },
          { text: 'Return the key', done: true, time: '3:20' },
          { text: 'Ms. Ortiz initials the log', done: true, time: '3:20' }
        ]
      },
      question: {
        prompt: 'Step 5 is blank, and Marcus did not check it. What is the missing step in this process?',
        options: [
          { text: 'Ask Ms. Ortiz', feedback: 'That is already Step 1.' },
          { text: 'Lock the case', correct: true, feedback: 'Correct. You unlock, take the item, then you must lock the case before you return the key. Marcus skipped it.' },
          { text: 'Take a photo of the trophy', feedback: 'That is not part of the process. Think about what comes after "Unlock" and "Remove".' },
          { text: 'Sign the key log', feedback: 'That is already Step 2.' }
        ]
      },
      fact: 'Marcus never locked the case. After 3:20 the trophy case was unlocked.'
    },

    E4: {
      title: 'Badge Swipes by Door, 3:00-4:00 PM',
      from: 'Ms. Ortiz (door system)',
      type: 'bar',
      level: 4,
      skill: 'Use one graphic to find information in another; compare data',
      requires: ['solved:E1'],
      requiresHint: 'First answer the floor plan question (E1) so you know which door is near the trophy case.',
      alt: 'Grouped bar chart of badge swipes in 10-minute blocks. Door A: 2 at 3:00, 0 at 3:10, 1 at 3:20, 0 at 3:30, 0 at 3:40, 1 at 3:50. Door B: 0, 0, 0, 1 at 3:30, 0, 0.',
      data: {
        categories: ['3:00', '3:10', '3:20', '3:30', '3:40', '3:50'],
        categoryNote: 'Each bar is a 10-minute block (3:30 means 3:30 to 3:39).',
        yLabel: 'Badge swipes',
        series: [
          { name: 'Door A (Main)', values: [2, 0, 1, 0, 0, 1] },
          { name: 'Door B (Lab)', values: [0, 0, 0, 1, 0, 0] }
        ]
      },
      question: {
        prompt: 'Use the floor plan to find the door nearest the trophy case. In this chart, when was THAT door swiped?',
        options: [
          { text: 'Door A, from 3:00 to 3:09', feedback: 'Door A is not near the trophy case. Check the floor plan.' },
          { text: 'Door B, from 3:30 to 3:39', correct: true, feedback: 'Correct. Door B is next to the case, and it was swiped only once: in the 3:30 block.' },
          { text: 'Door B, from 3:50 to 3:59', feedback: 'Look at the height of the Door B bars. Which block has a bar?' },
          { text: 'Door B was never swiped', feedback: 'Look carefully. One Door B bar is above zero.' }
        ]
      },
      fact: 'Someone badged in through Door B, right beside the trophy case, between 3:30 and 3:39.'
    },

    E5: {
      title: 'Trophy Case Shelf Weight Sensors',
      from: 'Priya',
      type: 'line',
      level: 6,
      skill: 'Compare two trends',
      alt: 'Line graph of shelf weight from 3:00 to 3:50. Shelf 1 (trophy) stays at 3.2 kg until 3:35, then drops to 0 kg at 3:36 and stays at 0. Shelf 2 (ribbons) stays at 0.9 kg until 3:17, drops to 0.7 kg at 3:18, and stays at 0.7 kg.',
      data: {
        xLabel: 'Time (PM)',
        yLabel: 'Weight (kg)',
        xMin: 0, xMax: 50, xStep: 10, xFormat: 'minutesAfter3',
        yMin: 0, yMax: 4, yStep: 1,
        series: [
          { name: 'Shelf 1 (trophy)', points: [[0, 3.2], [35, 3.2], [36, 0], [50, 0]] },
          { name: 'Shelf 2 (ribbons)', points: [[0, 0.9], [17, 0.9], [18, 0.7], [50, 0.7]] }
        ]
      },
      question: {
        prompt: 'Which statement correctly compares the two shelves?',
        options: [
          { text: 'Both shelves lost weight at the same time.', feedback: 'Find where each line drops. Are they at the same time?' },
          { text: 'Shelf 2 dropped a little at about 3:18. Shelf 1 dropped to zero at about 3:36.', correct: true, feedback: 'Correct. The ribbon (Shelf 2) left first. The trophy (Shelf 1) left about 18 minutes later.' },
          { text: 'Shelf 1 dropped first, then Shelf 2.', feedback: 'Read the x-axis under each drop. Which drop is further left?' },
          { text: 'Shelf 2 went down to zero.', feedback: 'Shelf 2 only dropped from 0.9 to 0.7 kg. It never reached zero.' }
        ]
      },
      fact: 'The trophy left Shelf 1 at about 3:36. This was after Marcus took the ribbon (3:18) and after Priya saw it (3:25).'
    },

    E6: {
      title: 'Library Check-ins, 3:00-4:00 PM',
      from: 'Ana',
      type: 'bar',
      level: 5,
      skill: 'Interpret data to draw a conclusion',
      alt: 'Bar chart of library check-ins per 10-minute block: 2 at 3:00, 0 at 3:10, 0 at 3:20, 0 at 3:30, 3 at 3:40, 1 at 3:50.',
      data: {
        categories: ['3:00', '3:10', '3:20', '3:30', '3:40', '3:50'],
        categoryNote: 'Each bar is a 10-minute block. Every student must scan an ID to enter.',
        yLabel: 'Students checked in',
        series: [{ name: 'Library check-ins', values: [2, 0, 0, 0, 3, 1] }]
      },
      question: {
        prompt: 'Sam says he arrived at the library at about 3:12 and stayed until 3:40. What does this chart suggest?',
        options: [
          { text: 'It supports Sam. Lots of students checked in.', feedback: 'Look at the blocks from 3:10 to 3:39. How many check-ins are there?' },
          { text: 'It does not support Sam. No one checked in from 3:10 to 3:39.', correct: true, feedback: 'Correct. If Sam went to the library at 3:12, there should be a check-in in that block. There is none.' },
          { text: 'Sam checked in at 3:40.', feedback: 'At 3:40 Sam signed back IN to Room 210. The 3:40 library check-ins were other students.' },
          { text: 'The chart cannot tell us anything about check-ins.', feedback: 'The chart counts every check-in, every 10 minutes.' }
        ]
      },
      fact: 'No one checked in at the library from 3:10 to 3:39. Sam\'s alibi is not supported.'
    },

    E7: {
      title: 'Team Vote: Who Keeps the Trophy This Summer?',
      from: 'Riley',
      type: 'pie',
      level: 3,
      skill: 'Locate information in a simple graphic',
      alt: 'Pie chart of 20 votes. Priya 45 percent, Riley 30 percent, Sam 15 percent, Marcus 10 percent.',
      data: {
        total: 20,
        slices: [
          { name: 'Priya', value: 9 },
          { name: 'Riley', value: 6 },
          { name: 'Sam', value: 3 },
          { name: 'Marcus', value: 2 }
        ]
      },
      question: {
        prompt: 'What percent of the team voted for Riley?',
        options: [
          { text: '45%', feedback: 'That is the largest slice. Whose is it?' },
          { text: '30%', correct: true, feedback: 'Correct. 6 out of 20 votes is 30%. Riley lost the vote to Priya.' },
          { text: '15%', feedback: 'That is Sam\'s slice.' },
          { text: '6%', feedback: 'Riley got 6 votes, but there are 20 votes total. 6 / 20 = ?' }
        ]
      },
      fact: 'Riley lost the vote (30%). That is a reason to be upset, but a motive is not proof.',
      redHerring: true
    }
  },

  // Facts needed before Ms. Ortiz will start the case review.
  readyWhen: ['solved:E1', 'solved:E2', 'solved:E3', 'solved:E4', 'solved:E5', 'solved:E6'],

  // The case review: the highest-level questions combine two graphics.
  review: [
    {
      id: 'R1', level: 6, skill: 'Interpret a trend',
      prompt: 'Ms. Ortiz asks: "When was the trophy taken?"',
      use: ['E5'],
      options: [
        { text: 'About 2:45, after the team photo', feedback: 'The sensor graph shows the trophy still on the shelf after 3:00.' },
        { text: 'About 3:18, when Marcus opened the case', feedback: 'At 3:18 only Shelf 2 (ribbons) dropped. Shelf 1 stayed at 3.2 kg.' },
        { text: 'About 3:36, when Shelf 1 dropped to zero', correct: true, feedback: 'Correct. The trophy weighed 3.2 kg. That weight left the shelf at 3:36.' },
        { text: 'About 3:50, when I noticed', feedback: 'The graph shows the shelf was already empty before 3:50.' }
      ]
    },
    {
      id: 'R2', level: 6, skill: 'Locate information in one graphic using another',
      prompt: '"How could someone open the case and reach it without walking past Jordan?"',
      use: ['E3', 'E4', 'E1'],
      options: [
        { text: 'The case was locked, so they used the key', feedback: 'Check the key checklist. Was the case locked after 3:20?' },
        { text: 'The case was unlocked after 3:20, and someone came in through Door B, right next to it, at 3:30-3:39', correct: true, feedback: 'Correct. You combined three graphics: the checklist, the floor plan and the badge chart.' },
        { text: 'They came in through Door A at 3:30', feedback: 'Door A had zero swipes in the 3:30 block.' },
        { text: 'They hid in the office', feedback: 'No graphic gives evidence for the office.' }
      ]
    },
    {
      id: 'R3', level: 7, skill: 'Make an inference from one graphic after finding information in another',
      prompt: '"The trophy left at 3:36. Using the hall pass log, who was signed OUT of Room 210 at 3:36?"',
      use: ['E5', 'E2'],
      options: [
        { text: 'Riley', feedback: 'Riley signed back in at 3:20.' },
        { text: 'Sam', correct: true, feedback: 'Correct. Sam was signed out from 3:10 to 3:40. 3:36 is inside that time.' },
        { text: 'Marcus', feedback: 'Marcus signed out at 3:40, after 3:36.' },
        { text: 'Priya', feedback: 'Priya was out from 2:30 to 2:40, long before.' }
      ]
    },
    {
      id: 'R4', level: 7, skill: 'Justify an inference',
      prompt: '"Sam says he was at the library. Why don\'t you believe that?"',
      use: ['E6', 'E4'],
      options: [
        { text: 'Because Sam is the team captain', feedback: 'That is not evidence.' },
        { text: 'Because Sam got only 15% of the vote', feedback: 'The vote is a red herring. It does not show where Sam was.' },
        { text: 'No one checked in at the library from 3:10 to 3:39, and the only Door B swipe was at 3:30-3:39, while Sam was signed out', correct: true, feedback: 'Correct. Two graphics together break Sam\'s alibi.' },
        { text: 'Because Jordan saw Sam at the case', feedback: 'Jordan said the case cannot be seen from the hall pass desk.' }
      ]
    },
    {
      id: 'R5', level: 7, skill: 'Identify and justify the most effective graphic',
      prompt: '"The principal wants ONE graphic that best shows WHEN the trophy was taken. Which should I send, and why?"',
      use: [],
      options: [
        { text: 'The pie chart, because it shows who wanted the trophy', feedback: 'A pie chart shows parts of a whole. It has no time information.' },
        { text: 'The floor plan, because it shows where the case is', feedback: 'A floor plan shows place, not time.' },
        { text: 'The shelf weight line graph, because a line graph shows change over time, minute by minute', correct: true, feedback: 'Correct. A line graph is the best graphic to show exactly when something changed.' },
        { text: 'The shelf weight line graph, because it has two colors', feedback: 'Right graphic, wrong reason. Why is a LINE graph good for showing "when"?' }
      ]
    }
  ],

  culpritPrompt: 'Who took the trophy?',
  culprit: 'sam',
  wrongCulprit: {
    riley: 'Riley had a motive, but Riley signed back in at 3:20. The trophy left at 3:36.',
    marcus: 'Marcus left the case unlocked, but the trophy left at 3:36, while Marcus was in the room. He signed out at 3:40.',
    priya: 'Priya was at the plant counter in the classroom. The only entry near the case was through Door B, from outside.',
    jordan: 'Jordan was at the hall pass desk the whole time and never signed out.',
    ana: 'Ana left the library at 3:00 to deliver books. No graphic places her near the case.'
  },

  ending: [
    'Sam looks at the floor. "OK. It was me."',
    '"I came back through Door B at 3:35. I saw the case was unlocked. I took the trophy and put it in my backpack. Then I signed back in at 3:40."',
    '"I wanted to take it to the engraving shop tonight. I wanted to add every team member\'s name before the awards assembly. It was supposed to be a surprise."',
    'Ms. Ortiz sighs. "That is a kind idea, Sam. But you have to ask first. And Marcus, the checklist exists for a reason."',
    'Case closed. You solved it by reading the graphics, not by guessing.'
  ]
};
