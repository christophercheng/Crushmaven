# Crushmaven
2013 CrushMaven.com Facebook Dating Site

WHAT WAS CRUSHMAVEN:

CrushMaven.com was a facebook powered dating site oriented for teens and young adults.  
It was launched in 2013 and was shut down in 2014 after failing to generate sufficient market traction.

CrushMaven, unlike traditional online dating sites, was geared towards people who already knew someone they were attracted to i.e. a crush. These users may have shared a friendship with their crush, were co-workers, or were already in another relationship.  Irregardless, they were uncomfortable 'making a move' and revealing their intentions unless they knew their attraction was mutual.

---
HOW IT WORKED:

Crushmaven users identified the facebook profiles of users they were attracted to. They were asked to provide information that Crushmaven could use to help get those people signed up (e.g. email, phone number, twitter account, etc.)

Once signed up, the facebook data of the user, their crush, and the relationship between them was analyzed
e.g. demographics like age, location, recent friendships, likes, etc.

The result of that facebook analsyis was a crush LINEUP: A lineup consists of 10 people that the crush would be asked to individually consider if were attracted to. Prior to, they are informed that at least one person in the lineup is already attracted to them.

They are notified if any of their marked attractions is mutually attracted to them.

---
THE LINEUP'S SOCIAL ALGORITHM:

There are many more considerations that were programmed into the creation of a line-up in order to protect the identity
or the originator of the crush, in case the attraction wasn't mutual.  In addition, lineup users were selected with the intent that new attractions would be discovered.  (This was the key viral growth ingredient.)

The timing of the notifications is played with in order to obfuscate who originated the attraction. If both the original user and their crush had a mutual attraction, then the timing of the notification could be delayed in order to give the crush the sense that they initiated the mutual attraction, when in reality, it was the other way around.

The selection of users in the lineup was carefully crafted to also obfuscate the originater or the attraction.  For example: if the crush was friends-of-friends but not a direct facebook friend of the user, then all of the lineup members would also have to be friends-of-friends.  Two other connection based relationships were programmed for: direct friends and users who don't have any mutual friends between them.

---

TECHNOLOGY IMPLEMENTED: CrushMaven was built on the Django/Python framework. 

It utilized a PostgreSQL and Memcached on backend and Jquery / Javscript on the front-end.
It also utilized python multi-threading in order to efficiently parse various facebook friends' lists in special
situations when those lists were only available by scraping public friend list pages.  (this may no longer be possible).

The social algorithms were implemented inside of Django views.  Interactivity on the front-end were implemented with client side Jquery Javascript and Ajax calls.

3rd Party integrations included the Facebook (GraphQL, Facebook Oath2 User Authentication), PayPal for payments.
