# Crushmaven
2013 CrushMaven.com Facebook Dating Site
http://crushmaven.herokuapp.com/

WHAT WAS CRUSHMAVEN:

CrushMaven.com was a facebook powered dating site oriented for teens and young adults.  
It was launched in 2013 and was shut down in 2014 after failing to generate sufficient market traction.

CrushMaven, unlike traditional online dating sites, was geared towards people who already knew someone they were attracted to i.e. a crush. These users may have shared a friendship with their crush, were co-workers, or were already in another relationship.  Irregardless, they were uncomfortable 'making a move' and revealing their intentions unless they knew their attraction was mutual.

---
HOW IT WORKED:

Crushmaven users identified the facebook profiles of users they were attracted to. They were asked to provide information that Crushmaven could use to help get those people signed up (e.g. email, phone number, twitter account, etc.)

Once signed up, the facebook data of the user, their crush, and the relationship between them was analyzed
e.g. demographics like age, location, recent friendships, likes, etc.

The result of that facebook analsyis was a crush LINEUP: A lineup consists of 10 people that the crush would be asked to individually consider if were attracted to. Prior to, they were informed that at least one person in the lineup was already attracted to them.

They were notified if any of their marked attractions was mutually attracted to them.

---
THE LINEUP'S SOCIAL ALGORITHM:

There were many considerations that were programmed into the creation of a line-up in order to protect the identity
of the originator of the crush, in case the attraction wasn't mutual.  In addition, lineup users were selected with the intent that new attractions would be discovered.  (This was the key viral growth ingredient.)

Here are a few examples of the lineup algorithm: 

If both the original user and their crush had a mutual attraction, then the timing of the notifications could be delayed in order to give the crush target the sense that they initiated the mutual attraction and were waiting to find out if the attraction was mutual.  In reality, they were the target of the attraction and not the other way around.

The selection of users in the lineup was carefully crafted to also obfuscate the originater of the attraction.  For example: if the crush was friends-of-friends but not a direct facebook friend of the user, then all of the lineup members would also have to be friends-of-friends.  Two other connection based relationships were programmed for: direct friends and users who don't have any mutual friends between them.

---

TECHNOLOGY IMPLEMENTED: CrushMaven was built on the Django/Python framework. 

It utilized a PostgreSQL database and Memcached caching on backend and Jquery / Javscript on the front-end.

The social algorithms were implemented inside of Django views.  Interactivity on the front-end were implemented with client side Jquery Javascript and Ajax calls.

3rd Party integrations included the Facebook (GraphQL, Facebook Oath2 User Authentication), PayPal for payments.

Python Multi-threading was utilized for the Facebook hack:

---

THE FACEBOOK HACK:

CrushMaven relied on a Facebook hack in order to build the lineups of users who were friends-of-friends with their crush.  At the time, Facebook limited what friendship data could be obtained through its Graph API (most likely for privacy reasons).  It also prohibited data scraping of public data by detecting and blocking parsing agents. The Crushmaven facebook hack overcame this hurdle.

CrushMaven was able to effectively parse the paginated pages of the public friends lists for most users. The key was going through a backdoor and utilizing an unpublished REST API endpoint that exposed this data. (This API endpoint was used as part of ajax calls to dynamically load friends into mobile facebook pages while a user scrolled through a friends list.)  This required python multi-threading in order to efficiently run.  And in order to call this endpoint as many times as I needed to (and not get blocked), I had to utilize a cookie that I had to continually refresh.  Essentially I was mocking as a new, different browser user on a frequent basis.  

Note, this functionality has most likely been prohibited and sealed off by Facebook in recent years.  But it worked great when it did :-)

---

Code Architecture and Implementation Flaws:

There were many.  The entire application was built in a hurried MVP approach with the intent of being completely re-built if the business took off.  Here is just a sampling of the problems with this site:

1.  The Jquery javascript front end code is a complete mess.  If this were re-written in 2018, a front-end framework like React would be used.  

Note: all of the javscript functionality was written before I  understood how to program in a functional programming language and how to utilize the related features of Javascript, in particular how functions act as first class citizens.  

2.  The single responsibility principle was abused all over the place.  Functions are unnecessarily long and contain too many unrlelated purposes.

3.  There are zero unit tests.  Again, this goes back to the hurried MVP approach.  But if I had to built this in 2018, particularly with a front-end framework like React, I would have included unit tests built on a simple testing framework like Jest/Enzyme.

4.  The CSS styling did not use any newer CSS technologies like SASS.  It is also a complete mess with an over-abundance of !important declarations.  It is also not-responsive.  If re-written today, I would probably expirement utilizing a CSS grid to implement reponsiveness.

Luckily, the django framework and it's separated organization of code by concern e.g. views vs models, helped organize much of the back-end code.


