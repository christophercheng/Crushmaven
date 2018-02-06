# Crushmaven
2013 CrushMaven.com Facebook Dating Site

WHAT WAS CRUSHMAVEN:

CrushMaven.com was a facebook powered dating site oriented for teens and young adults.  
It was launchedi in 2013 and was shut down in 2014 after failing to generate sufficient market traction.

CrushMaven, unlike traditional online dating sites, was geared towards people who already knew someone they were attracted to
but were uncomfortable making a move unless they knew the target of their attraction was similarly attracted to them. 
e.g. a co-worker or someone they've shared a friendship with.

---
HOW IT WORKED:

Crushmaven users identified the facebook profiles of users they were attracted to and provided,
and they provided information that Crushmaven could use to help get those people signed up (email, phone number, twitter account, etc.)

Once signed up, the facebook data of the user, their crush, and the relationship between then is analyzed
e.g. demographics like age, location, recent friendships, likes, etc.

Subsequently a LINEUP is created: A lineup consists of 10 people that the crush would be asked to go through
and mark if were attracted to them or not. They are informed that at least one person in the lineup is already attracted to them.
They are notified if any of their marked attractions is mutual.

The timing of the notifications is played with in order to obfuscate who originated the attraction. The selection of users in the
lineup is carefully crafted to also obfuscate the originater or the attraction.  For example.  If the crush is friends-of-friends
but not directly facebook friends with the user, then all of the lineup members would also have to be friends-of-friends.

There are many more considerations that were programmed into the creation of a line-up in order to protect the identity
or the originator of the crush, in case the attraction wasn't mutual.

---

TECHNOLOGY IMPLEMENTED: CrushMaven was built on the Django/Python framework. 

It utilized a PostgreSQL and Memcached on backend and Jquery / Javscript on the front-end.
It also utilized python multi-threading in order to efficiently parse various facebook friends' lists in special
situations when those lists were only available by scraping public friend list pages.  (this may no longer be possible).
