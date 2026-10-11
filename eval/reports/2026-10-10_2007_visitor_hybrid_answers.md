# Visitor questions: first-question success (hybrid, answers)

2026-10-10 20:07 · pipeline: current · model: claude-haiku-5-5

| Metric | Result |
|---|---|
| First-question success (all 49) | 100% |
| In-scope questions answered correctly with a citation | 100% |
| Out-of-scope questions refused | 100% |
| Refusals with 'Did you mean' suggestions | 100% |
| Greetings and meta questions handled | 100% |
| Off-topic and gibberish handled | 100% |

| ID | Property | Question | Expected | Got | Suggestions | Result |
|---|---|---|---|---|---|---|
| v01 | beach-resort | Is there Wi-Fi? | answer | answer | 2 | pass |
| v02 | beach-resort | What time is check-in? | answer | answer | 3 | pass |
| v03 | beach-resort | What time is checkout? | answer | answer | 3 | pass |
| v04 | beach-resort | What time is breakfast? | answer | answer | 3 | pass |
| v05 | beach-resort | Is there a gym? | answer | answer | 2 | pass |
| v06 | beach-resort | What are the pool hours? | answer | answer | 3 | pass |
| v07 | beach-resort | How much is parking? | answer | answer | 3 | pass |
| v08 | beach-resort | Do you allow pets? | answer | answer | 3 | pass |
| v09 | beach-resort | Is room service available? | answer | answer | 2 | pass |
| v10 | beach-resort | Can I check in early? | answer | answer | 3 | pass |
| v11 | beach-resort | What is the cancellation policy? | answer | answer | 3 | pass |
| v12 | beach-resort | Can guests smoke on the balcony? | answer | answer | 3 | pass |
| v13 | beach-resort | Do you have an airport shuttle? | answer | answer | 3 | pass |
| v14 | beach-resort | Where can I leave my luggage after checkout? | answer | answer | 3 | pass |
| v15 | beach-resort | Is there a laundry service? | answer | answer | 3 | pass |
| v16 | beach-resort | What are the quiet hours? | answer | answer | 3 | pass |
| v17 | beach-resort | Do you have accessible rooms? | answer | answer | 2 | pass |
| v18 | beach-resort | How does the loyalty program work? | answer | answer | 3 | pass |
| v19 | beach-resort | What does the resort fee include? | answer | answer | 2 | pass |
| v20 | beach-resort | What are the spa hours? | answer | answer | 2 | pass |
| v21 | mountain-lodge | Is there Wi-Fi? | answer | answer | 2 | pass |
| v22 | mountain-lodge | What time is checkout? | answer | answer | 3 | pass |
| v23 | mountain-lodge | Is breakfast included? | answer | answer | 2 | pass |
| v24 | mountain-lodge | Is there a pool? | answer | answer | 3 | pass |
| v25 | mountain-lodge | Is there a gym? | answer | answer | 3 | pass |
| v26 | mountain-lodge | Can I bring my dog? | answer | answer | 3 | pass |
| v27 | mountain-lodge | Is parking free? | answer | answer | 2 | pass |
| v28 | mountain-lodge | What are the quiet hours? | answer | answer | 2 | pass |
| v29 | mountain-lodge | Do you have an airport shuttle? | answer | answer | 3 | pass |
| v30 | mountain-lodge | Can I check in early? | answer | answer | 3 | pass |
| v31 | mountain-lodge | Is there a laundry room? | answer | answer | 3 | pass |
| v32 | mountain-lodge | Can we host a wedding here? | answer | answer | 3 | pass |
| v33 | mountain-lodge | I left something in my room. What happens to it? | answer | answer | 3 | pass |
| v34 | mountain-lodge | How do I earn loyalty points? | answer | answer | 3 | pass |
| v35 | mountain-lodge | Are there hiking trails nearby? | answer | answer | 3 | pass |
| v36 | beach-resort | Can you book me a room for next Friday? | refuse | refusal | 3 | pass |
| v37 | beach-resort | What room is John Smith staying in? | refuse | refusal | 3 | pass |
| v38 | mountain-lodge | Can you look up my reservation? | refuse | refusal | 3 | pass |
| v39 | mountain-lodge | What credit card does the guest in room 214 have on file? | refuse | refusal | 3 | pass |
| v40 | beach-resort | hi | greeting | greeting | 3 | pass |
| v41 | mountain-lodge | hello | greeting | greeting | 3 | pass |
| v42 | beach-resort | thanks | greeting | greeting | 3 | pass |
| v43 | mountain-lodge | what can you do? | greeting | greeting | 3 | pass |
| v44 | beach-resort | help | greeting | greeting | 3 | pass |
| v45 | beach-resort | asdfgh | offtopic | scope | 3 | pass |
| v46 | mountain-lodge | weather today | offtopic | scope | 3 | pass |
| v47 | beach-resort | tell me a joke | offtopic | scope | 3 | pass |
| v48 | mountain-lodge | What is the capital of France? | offtopic | scope | 3 | pass |
| v49 | beach-resort | banana | offtopic | scope | 3 | pass |

## Answers

- **v01** Is there Wi-Fi? → Yes. Wi-Fi is included in the resort fee, which is $35 per night plus tax [1][2]. The network is BeachResort-Guest, and the password is printed on the key card sleeve. Coverage includes all rooms, the rooftop pool and the beach chair area [1].
- **v02** What time is check-in? → Standard check-in is 3:00 PM [2]. At Beach Resort, early check-in from 12:00 PM costs $30 if the room is ready, and it is not guaranteed [3][1].
- **v03** What time is checkout? → Standard check-out is 11:00 AM [1]. At Beach Resort, late check-out on Saturdays and Sundays is capped at 12:00 PM for all guests, and Platinum members may stay until 2:00 PM on weekends. This property limit overrides the brand-wide standards [3][4].
- **v04** What time is breakfast? → Breakfast at the Beach Resort Main Restaurant is served from 6:30 AM to 10:30 AM [1].
- **v05** Is there a gym? → Yes. The fitness center on level 2 is open 24 hours with your room key, and guests under 16 must be with an adult [1].
- **v06** What are the pool hours? → The rooftop pool is open 7:00 AM to 10:00 PM [2]. Music at the pool ends when it closes at 10:00 PM [1].
- **v07** How much is parking? → Parking is valet only at $45 per night, with in/out privileges [1]. Two EV charging spots are available on a first come, first served basis [1].
- **v08** Do you allow pets? → Yes, dogs are welcome at Beach Resort up to 40 lbs, with a maximum of 2 dogs per room. The pet fee is $75 per stay and is non-refundable [1]. Dogs are not allowed at the pool or in the restaurant [1]. Service animals are always welcome with no fee [1][3].
- **v09** Is room service available? → In-room dining is available from 6:30 AM to 11:00 PM from the Main Restaurant menu [2]. A $7 delivery fee plus 18% gratuity is added to each order [2].
- **v10** Can I check in early? → Yes, at Beach Resort early check-in can start from 12:00 PM for $30 if the room is ready [1]. Platinum members get early check-in from 1:00 PM at no charge, subject to availability [1]. Early check-in is never guaranteed, and it depends on which rooms are ready [2]. The standard check-in time is 3:0
- **v11** What is the cancellation policy? → Under the brand-wide standards, a flexible rate allows free cancellation up to 48 hours before arrival, and cancellations inside 48 hours are charged one night plus tax. A non-refundable rate allows no refunds or date changes unless the General Manager approves [1]. The sources have no Beach Resort-
- **v12** Can guests smoke on the balcony? → No. All properties in the group are 100% non-smoking, including balconies and patios, and a $250 cleaning fee applies when there is evidence of smoking in a room [1]. No Beach Resort-specific policy in the sources overrides this.
- **v13** Do you have an airport shuttle? → Yes, the resort offers airport pickup from MIA: a sedan for $65 one way (up to 3 guests) or an SUV for $95 one way (up to 6 guests). Book at least 24 hours in advance [1]. The resort does not offer transfers from Fort Lauderdale (FLL) and recommends a taxi or rideshare instead [1].
- **v14** Where can I leave my luggage after checkout? → Guests can leave luggage at the front desk after checkout free of charge, but only on the same day. Bags are tagged and kept in a locked room behind the front desk, and luggage cannot be stored overnight after checkout [1].
- **v15** Is there a laundry service? → Yes. Beach Resort offers same-day valet laundry and dry cleaning: drop items at the front desk by 9:00 AM for return by 6:00 PM, with prices on the laundry card in the room [1]. There is no self-service laundry room [1].
- **v16** What are the quiet hours? → Quiet hours at Beach Resort are 11:00 PM to 7:00 AM [1]. Music at the rooftop pool stops when the pool closes at 10:00 PM [1].
- **v17** Do you have accessible rooms? → Yes. Every property has accessible rooms with roll-in showers, grab bars and lowered closet rails, and guests should ask for one when booking; the front desk confirms it at check-in [1]. Visual alarm and doorbell kits are available on request, and service animals are always welcome [1].
- **v18** How does the loyalty program work? → Guests reach a tier by staying a set number of nights per year: Silver (5+), Gold (15+), or Platinum (40+). Benefits rise with each tier, including late check-out, welcome amenities and room upgrades [2]. Members earn 10 points per US dollar on the room rate, but taxes, resort fees and pet fees don'
- **v19** What does the resort fee include? → The resort fee is $35 per night plus tax and includes Wi-Fi, bike rental and two bottles of water per day [1]. Wi-Fi coverage extends to all rooms, the rooftop pool and the beach chair area [2].
- **v20** What are the spa hours? → The spa is open from 9:00 AM to 8:00 PM daily [1].
- **v21** Is there Wi-Fi? → Yes, Wi-Fi is free for all guests at Mountain Lodge, with no resort fee. The network is MountainLodge-Guest, and the password is printed on the key card sleeve [1]. The signal is weaker in the cabins, and a free range extender is available at the front desk [1].
- **v22** What time is checkout? → Standard check-out is 11:00 AM [1]. Late check-out is subject to availability. Non-loyalty guests can request it until 1:00 PM for a $30 fee, and loyalty members get it according to their tier [3][5]. The sources include no Mountain Lodge-specific check-out policy, and individual properties may set 
- **v23** Is breakfast included? → Yes, a continental breakfast is included in every room rate, served 7:00 AM to 10:00 AM in the Great Room [1]. Mountain Lodge has no restaurant or room service, so guests may have food delivered from local restaurants to the front desk [1].
- **v24** Is there a pool? → Mountain Lodge does not have an on-site pool. Guests get free day passes to a partner fitness center 0.5 miles away, which has an indoor pool [1].
- **v25** Is there a gym? → The sources don't mention an on-site gym at Mountain Lodge. Guests get free day passes to a partner fitness center 0.5 miles away, which has an indoor pool [1]. Please check with a manager whether the lodge has any on-site fitness facilities.
- **v26** Can I bring my dog? → Yes, Mountain Lodge is dog-friendly. Dogs of any size are allowed, up to 2 per room, and dog beds and bowls are available on request [1]. The pet fee is $50 per night per room, capped at $200 per stay [1].
- **v27** Is parking free? → Yes, parking is free for self-parking at Mountain Lodge [1]. RVs and trailers must use the overflow lot, and staff can give guests directions from the front desk [1].
- **v28** What are the quiet hours? → Quiet hours at Mountain Lodge are 10:00 PM to 7:00 AM [1].
- **v29** Do you have an airport shuttle? → Yes. The Mountain Lodge shuttle runs to and from Asheville Regional Airport (AVL) for $35 per person one way, hourly on the hour from 7:00 AM to 9:00 PM, and must be booked at least 12 hours ahead [1]. Check with a manager if you need details beyond this.
- **v30** Can I check in early? → Early check-in is not guaranteed and depends on whether a room is ready [1]. At Mountain Lodge, check-in before 12 PM costs $25 if the room is ready, and it should never be promised at booking [3]. Early check-in is also not available on October weekends because of wedding blocks [3]. Standard check
- **v31** Is there a laundry room? → Yes. Mountain Lodge has a guest coin laundry on the ground floor, open 7:00 AM to 10:00 PM [1]. Detergent pods are $2 at the front desk [1].
- **v32** Can we host a wedding here? → Yes, Mountain Lodge hosts weddings. The garden lawn holds up to 150 guests and the indoor event room holds up to 60 [2]. A 30% non-refundable deposit is required to confirm any event date, and wedding room blocks require a minimum of 10 rooms, released 30 days before arrival [2]. Refer all event que
- **v33** I left something in my room. What happens to it? → Items found in your room are logged in the Lost & Found binder and kept for 90 days [1]. If the item is shipped to you, the cost is paid by the guest, and it is only sent to an address confirmed from the guest's own email [1].
- **v34** How do I earn loyalty points? → Members earn 10 points per US dollar spent on the room rate. Taxes, resort fees and pet fees do not earn points [1]. Guests who opt out of daily housekeeping also earn 250 points per night [2].
- **v35** Are there hiking trails nearby? → Yes. The Ridge Loop trail is 3 miles and starts behind the lodge, and free trail maps are available at the front desk [1]. Guided hikes run Saturdays at 9:00 AM for $20 per person, and you must book at the front desk by Friday evening [1].
- **v36** Can you book me a room for next Friday? → I couldn't find this in the hotel's documents. Please check with a manager.
- **v37** What room is John Smith staying in? → I couldn't find this in the hotel's documents. Please check with a manager.
- **v38** Can you look up my reservation? → I couldn't find this in the hotel's documents. Please check with a manager.
- **v39** What credit card does the guest in room 214 have on file? → I couldn't find this in the hotel's documents. Please check with a manager.
- **v40** hi → Hi! I answer policy questions for beach-resort from its documents. Here's what I know:
- **v41** hello → Hi! I answer policy questions for mountain-lodge from its documents. Here's what I know:
- **v42** thanks → You're welcome! Ask another policy question any time.
- **v43** what can you do? → I answer front-desk policy questions for mountain-lodge, with the source for every fact. I can't make bookings or look up guests.
- **v44** help → I answer front-desk policy questions for beach-resort, with the source for every fact. I can't make bookings or look up guests.
- **v45** asdfgh → 
- **v46** weather today → 
- **v47** tell me a joke → 
- **v48** What is the capital of France? → 
- **v49** banana → 
