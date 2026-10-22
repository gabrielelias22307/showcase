// Optional practice: WorkKeys Applied Math (Levels 3-7).
//
// Turned on with the "Extra practice" switches (start screen or
// Notebook > My progress), or locked by the teacher with ?practice=math.
// These tasks never change the mystery. Each one is handed out by a
// character in the room, and each wrong option explains the mistake.
//
// Levels follow ACT's Applied Math level descriptions (see STANDARDS.md).
// On the real test students may use a calculator and a formula sheet,
// so the game shows a formula sheet with every task.

export default {
  id: 'math',
  label: 'Applied Math',
  icon: '📐',
  taskWord: 'Math task',
  description: 'Workplace math problems: money, rates, percents, area and volume.',
  calculatorNote: 'You may use a calculator, just like on the real test.',
  formulaSheet: [
    'Rectangle: area = length × width; perimeter = 2 × (length + width)',
    'Box (rectangular solid): volume = length × width × height',
    'Circle: area = π × r²; circumference = 2 × π × r',
    'Cylinder: volume = π × r² × height',
    'π ≈ 3.14',
    '100 centimeters (cm) = 1 meter (m)',
    '1,000 cubic centimeters (cm³) = 1 liter (L)',
    '60 minutes = 1 hour'
  ],

  items: {
    AM1: {
      level: 3, skill: 'Add prices and find the change',
      from: 'jordan', title: 'School store change',
      intro: 'I also run the school store table after school. Can you check my math?',
      prompt: 'A student buys 1 pencil for $0.75 and 1 eraser for $0.50. The student pays with a $5.00 bill. How much change should Jordan give back?',
      options: [
        { text: '$4.25', feedback: 'That is $5.00 minus only the pencil. Add both prices first: $0.75 + $0.50.' },
        { text: '$3.75', correct: true, feedback: 'Correct. $0.75 + $0.50 = $1.25, and $5.00 − $1.25 = $3.75.' },
        { text: '$1.25', feedback: 'That is the total cost, not the change. Subtract the total from $5.00.' },
        { text: '$4.50', feedback: 'That is $5.00 minus only the eraser. Add both prices first.' }
      ]
    },

    AM2: {
      level: 3, skill: 'Change a fraction to a percent',
      from: 'riley', title: 'Safety quiz',
      intro: 'Ms. Ortiz wants to know how many of us passed the safety quiz.',
      prompt: '3 out of 4 robotics team members passed the safety quiz. What percent of the team passed?',
      options: [
        { text: '34%', feedback: 'That just puts the 3 and the 4 side by side. Divide: 3 ÷ 4.' },
        { text: '43%', feedback: 'That puts the 4 and the 3 side by side. Divide: 3 ÷ 4.' },
        { text: '75%', correct: true, feedback: 'Correct. 3 ÷ 4 = 0.75, and 0.75 = 75%.' },
        { text: '7.5%', feedback: 'You divided correctly (0.75), but 0.75 = 75%. Move the decimal point two places to the right.' }
      ]
    },

    AM3: {
      level: 4, skill: 'Find an average with decimals',
      from: 'marcus', title: 'Robot test runs',
      intro: 'I timed our robot on the practice course four times.',
      graphic: {
        type: 'table', title: 'Practice course times',
        alt: 'Table of four practice runs. Run 1: 12.4 seconds. Run 2: 11.8 seconds. Run 3: 13.0 seconds. Run 4: 12.2 seconds.',
        data: {
          columns: ['Run', 'Time (seconds)'],
          rows: [['1', '12.4'], ['2', '11.8'], ['3', '13.0'], ['4', '12.2']],
          note: 'Times measured with a stopwatch.'
        }
      },
      prompt: 'What is the average (mean) time for the four runs?',
      options: [
        { text: '49.4 seconds', feedback: 'That is the total of all four runs. Now divide by the number of runs.' },
        { text: '12.4 seconds', feedback: 'That is only Run 1. Add all four times, then divide by 4.' },
        { text: '12.3 seconds', feedback: 'That is the middle value (median). The average is the total divided by 4.' },
        { text: '12.35 seconds', correct: true, feedback: 'Correct. 12.4 + 11.8 + 13.0 + 12.2 = 49.4, and 49.4 ÷ 4 = 12.35.' }
      ]
    },

    AM4: {
      level: 4, skill: 'Use a rate',
      from: 'ortiz', title: '3D printer wheels',
      intro: 'While you are here: I need to plan time on the 3D printer.',
      prompt: 'The 3D printer makes 3 robot wheels in 45 minutes. At the same rate, how long will it take to make 8 wheels?',
      options: [
        { text: '120 minutes (2 hours)', correct: true, feedback: 'Correct. 45 ÷ 3 = 15 minutes per wheel, and 15 × 8 = 120 minutes.' },
        { text: '360 minutes', feedback: 'That is 45 × 8. But 45 minutes is the time for 3 wheels, not 1.' },
        { text: '24 minutes', feedback: 'That is 3 × 8. Find the minutes for one wheel first: 45 ÷ 3.' },
        { text: '90 minutes', feedback: 'Two batches of 3 wheels make only 6 wheels. Find the time for one wheel first.' }
      ]
    },

    AM5: {
      level: 5, skill: 'Find the best deal using a percent discount',
      from: 'sam', title: 'Poster printing',
      intro: 'I have to print our team poster. Which shop should I use?',
      prompt: 'Shop A charges $24 for the poster, with a 25% student discount. Shop B charges $20, with no discount. Which shop is cheaper, and by how much?',
      options: [
        { text: 'Shop B, by $4', feedback: 'You forgot Shop A\'s discount. Find 25% of $24 and subtract it.' },
        { text: 'Shop A, by $2', correct: true, feedback: 'Correct. 25% of $24 is $6, so Shop A costs $18. $20 − $18 = $2.' },
        { text: 'Shop A, by $6', feedback: '$6 is the discount. Compare the final prices: $18 and $20.' },
        { text: 'They cost the same', feedback: 'Find Shop A\'s price after the discount: $24 − (25% of $24).' }
      ]
    },

    AM6: {
      level: 5, skill: 'Find the area of a rectangle, then the cost',
      from: 'priya', title: 'Waterproof mat',
      intro: 'The plant water drips on the shelf. I want to cover it with a mat.',
      prompt: 'The top of the plant shelf is 0.7 meters wide and 4 meters long. Waterproof mat costs $5 per square meter. How much will enough mat to cover the top cost?',
      options: [
        { text: '$47.00', feedback: 'You used the perimeter (the distance around). Covering a surface needs the area: length × width.' },
        { text: '$2.80', feedback: '2.8 is the area in square meters. Now multiply by $5 per square meter.' },
        { text: '$14.00', correct: true, feedback: 'Correct. Area = 0.7 × 4 = 2.8 square meters, and 2.8 × $5 = $14.00.' },
        { text: '$23.50', feedback: 'You added the sides (0.7 + 4). For area, multiply them.' }
      ]
    },

    AM7: {
      level: 6, skill: 'Work a percent backward (reverse percent)',
      from: 'ana', title: 'Book sale',
      intro: 'The library bought a set of robotics books on sale. I need the original price for our records.',
      prompt: 'After a 20% discount, the book set cost $64. What was the price before the discount?',
      options: [
        { text: '$80.00', correct: true, feedback: 'Correct. After a 20% discount you pay 80%. $64 ÷ 0.80 = $80.' },
        { text: '$76.80', feedback: 'That adds 20% of $64. But the 20% was taken from the original price, not from $64. Divide $64 by 0.80.' },
        { text: '$51.20', feedback: 'That takes another 20% off. The original price must be MORE than $64.' },
        { text: '$84.00', feedback: '20% is a percent, not $20. $64 is 80% of the original price.' }
      ]
    },

    AM8: {
      level: 6, skill: 'Find the volume of a box',
      from: 'marcus', title: 'Packing the parts bin',
      intro: 'I have to pack sensor boxes into a bin in the parts cabinet.',
      prompt: 'The bin is 40 cm long, 30 cm wide and 20 cm tall. Each sensor box is 10 cm long, 10 cm wide and 5 cm tall. If the boxes pack in perfectly, how many sensor boxes fit in the bin?',
      options: [
        { text: '12', feedback: 'That is one layer on the bottom of the bin. How many 5 cm layers fit in 20 cm?' },
        { text: '4', feedback: 'That is the number of layers. Multiply by the boxes in each layer.' },
        { text: '240', feedback: 'You divided the bin\'s volume by the top of a box (100 cm²). Divide by the box\'s volume: 10 × 10 × 5.' },
        { text: '48', correct: true, feedback: 'Correct. Bin: 40 × 30 × 20 = 24,000 cm³. Box: 10 × 10 × 5 = 500 cm³. 24,000 ÷ 500 = 48.' }
      ]
    },

    AM9: {
      level: 7, skill: 'Find a weighted average',
      from: 'sam', title: 'Competition score',
      intro: 'The judges sent our scores. The parts don\'t count the same.',
      graphic: {
        type: 'table', title: 'Judges\' score sheet',
        alt: 'Table with three parts. Design: weight 50%, score 80. Programming: weight 30%, score 90. Presentation: weight 20%, score 70.',
        data: {
          columns: ['Part', 'Weight', 'Score'],
          rows: [['Design', '50%', '80'], ['Programming', '30%', '90'], ['Presentation', '20%', '70']],
          note: 'Final score = weighted average of the three parts.'
        }
      },
      prompt: 'What is the team\'s final (weighted) score?',
      options: [
        { text: '80', feedback: 'That is the plain average (240 ÷ 3). It treats every part the same. Use the weights.' },
        { text: '78', feedback: 'You matched the weights to the wrong parts. Design is worth 50%.' },
        { text: '81', correct: true, feedback: 'Correct. 0.50 × 80 + 0.30 × 90 + 0.20 × 70 = 40 + 27 + 14 = 81.' },
        { text: '240', feedback: 'That is the total of the three scores, not the final score.' }
      ]
    },

    AM10: {
      level: 7, skill: 'Find the volume of a cylinder and change units',
      from: 'ortiz', title: 'Robot water tank',
      intro: 'Our new robot carries water in a round tank. The rules limit how much water it can carry.',
      prompt: 'The tank is a cylinder with a radius of 5 cm and a height of 12 cm. About how many liters does it hold? (Round to the nearest tenth.)',
      options: [
        { text: '3.8 liters', feedback: 'You used 10 cm (the diameter) as the radius. The radius is 5 cm.' },
        { text: '0.9 liters', correct: true, feedback: 'Correct. 3.14 × 5² × 12 = 942 cm³, and 942 ÷ 1,000 = 0.9 liters.' },
        { text: '9.4 liters', feedback: 'The volume is 942 cm³. 1,000 cm³ = 1 liter, so divide by 1,000, not 100.' },
        { text: '0.4 liters', feedback: 'You used 2 × π × r × h. That is the area of the side, not the volume. Use π × r² × h.' }
      ]
    }
  }
};
