import mysql.connector

con = mysql.connector.connect(host='localhost', user='root', password='root', database='kinetic_db')
cur = con.cursor()

events = [
    ('Tech Symposium 2026', '2026-08-10', '5-6',
     'A cutting-edge symposium where students showcase innovative projects in AI, ML, and robotics.',
     'Students will gain exposure to real-world tech applications and network with industry professionals.',
     'Main Auditorium', 200, None),
    ('Cultural Fest: Rhythm Night', '2026-08-15', 'all',
     'A vibrant evening of music, dance, and art celebrating the diverse cultures of our campus.',
     'Students will experience intercultural exchange and discover hidden talents.',
     'Open Air Theatre', 500, None),
    ('Hackathon 72H', '2026-08-20', '3-4',
     'A 72-hour coding marathon where teams build solutions for real-world problems.',
     'Participants will win prizes and get internship opportunities from sponsor companies.',
     'CS Lab Block B', 100, None),
    ('Leadership Summit', '2026-08-25', '7-8',
     'A full-day summit featuring talks from alumni leaders and interactive workshops on professional growth.',
     'Students will leave with a personal leadership roadmap and industry connections.',
     'Conference Hall', 150, None),
    ('Science Exhibition', '2026-09-01', '1-2',
     'Freshers present their first-year projects in a science fair format judged by faculty and industry experts.',
     'Winners receive academic credits and certificates.',
     'Science Block', 300, None),
    ('Sports Day 2026', '2026-09-05', 'all',
     'The annual inter-department sports tournament featuring cricket, football, basketball, and athletics.',
     'Foster team spirit and celebrate athletic excellence across all departments.',
     'Sports Ground', 1000, None),
    ('World Innovation Day 2026', '2026-08-12', 'all',
     'Global celebration of human creativity, innovation, and technological breakthroughs across campus disciplines.',
     'Exhibiting student innovations, tech prototypes, and creative projects.',
     'Main Auditorium', 250, None),
]

cur.executemany(
    'INSERT INTO events (title, event_date, semester, purpose, outcome, location, capacity, banner_image) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)',
    events
)
con.commit()
print(f'Inserted events successfully!')

cur.execute('SELECT id, title FROM events ORDER BY id DESC LIMIT 6')
for row in cur.fetchall():
    cur2 = con.cursor()
    cur2.execute('INSERT INTO notifications (event_id, message) VALUES (%s, %s)',
                 (row[0], 'New Event Archive Released: ' + row[1]))
    con.commit()
    cur2.close()

cur.close()
con.close()
print('Done! All events and notifications added.')
