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

They were notified if any of their marked attractions was mutually attracted to them.

---
THE LINEUP'S SOCIAL ALGORITHM:

There are many more considerations that were programmed into the creation of a line-up in order to protect the identity
or the originator of the crush, in case the attraction wasn't mutual.  In addition, lineup users were selected with the intent that new attractions would be discovered.  (This was the key viral growth ingredient.)

Here are a few examples of the lineup algorithm: 

If both the original user and their crush had a mutual attraction, then the timing of the notifications could be delayed in order to give the crush target the sense that they initiated the mutual attraction and were waiting to find out if the attraction was mutual.  In reality, they were the target of the attraction and not the other way around.

The selection of users in the lineup was carefully crafted to also obfuscate the originater or the attraction.  For example: if the crush was friends-of-friends but not a direct facebook friend of the user, then all of the lineup members would also have to be friends-of-friends.  Two other connection based relationships were programmed for: direct friends and users who don't have any mutual friends between them.

---

TECHNOLOGY IMPLEMENTED: CrushMaven was built on the Django/Python framework. 

It utilized a PostgreSQL database and Memcached caching on backend and Jquery / Javscript on the front-end.

The social algorithms were implemented inside of Django views.  Interactivity on the front-end were implemented with client side Jquery Javascript and Ajax calls.

3rd Party integrations included the Facebook (GraphQL, Facebook Oath2 User Authentication), PayPal for payments.

Python Multi-threading was utilized for the Facebook hack:

---

THE FACEBOOK HACK:

CrushMaven relied on a Facebook hack in order to build the lineups of users who were friends-of-friends with their crush.  At the time, Facebook, limited what friendship data could be obtained (most likely for privacy reasons).  In order to find other friends-of-friends to populate a linup with, CrushMaven could not rely on the Facebook GraphQL API.  And data scraping of public data was detected and blocked by Facebook. The Crushmaven hack overcame this hurdle.

CrushMaven was able to effectively parse the paginated pages of the public friends lists for both users. The key was going through a backdoor and utilizing a deprecated REST API endpoint that exposed this data. This required python multi-threading in order to efficiently run.  And in order to call this endpoint as many times as I needed to (and not get blocked), I had to utilize a cookie that I had to continually refresh.  Essentially I was mocking as a new, different browser user on a frequent basis.  

Note, this functionality has most likely been prohibited and sealed off by Facebook in recent years.  But it worked great when it did :-)


