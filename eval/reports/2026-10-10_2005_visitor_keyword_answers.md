# Visitor questions: first-question success (keyword, answers)

2026-10-10 20:05 · pipeline: current · model: claude-haiku-5-5

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

- **v01** Is there Wi-Fi? → Yes, Wi-Fi is included in the resort fee, which is $35 per night plus tax [2]. The network is BeachResort-Guest, with the password printed on the key card sleeve, and coverage includes all rooms, the rooftop pool and the beach chair area [1].
- **v02** What time is check-in? → Standard check-in is 3:00 PM [3]. Beach Resort offers early check-in from 12:00 PM for $30 if the room is ready, and it is not guaranteed [2][1].
- **v03** What time is checkout? → Standard check-out is 11:00 AM [1]. At Beach Resort, late check-out on Saturdays and Sundays is capped at 12:00 PM for all guests, and Platinum members can stay until 2:00 PM on weekends [4]. Late check-out is always subject to availability [3].
- **v04** What time is breakfast? → Breakfast at the Beach Resort's Main Restaurant is served from 6:30 AM to 10:30 AM [1].
- **v05** Is there a gym? → Yes. The fitness center is on level 2 and is open 24 hours with your room key. Guests under 16 must be with an adult. [1]
- **v06** What are the pool hours? → The rooftop pool is open 7:00 AM to 10:00 PM [2]. Music at the pool ends when it closes at 10:00 PM [1].
- **v07** How much is parking? → Valet parking costs $45 per night, with in/out privileges [1]. There are also two EV charging spots, first come first served [1].
- **v08** Do you allow pets? → Yes, dogs are welcome at Beach Resort up to 40 lbs, with a maximum of 2 dogs per room and a $75 non-refundable pet fee per stay [1]. Dogs are not allowed at the pool or in the restaurant, and service animals are welcome with no fee [1].
- **v09** Is room service available? → Yes. Room service at Beach Resort is available from 6:30 AM to 11:00 PM, from the Main Restaurant menu [1][3]. A $7 delivery fee and 18% gratuity are added to each order [1][3].
- **v10** Can I check in early? → Yes, if a room is ready. At Beach Resort, early check-in from 12:00 PM costs $30, and it isn't guaranteed [1]. Platinum members can check in from 1:00 PM at no charge, subject to availability [1]. This property's fee and earliest time override the brand-wide defaults [2].
- **v11** What is the cancellation policy? → Brand-wide, flexible rates allow free cancellation up to 48 hours before arrival, and cancellations inside 48 hours are charged one night plus tax. Non-refundable rates allow no refunds or date changes unless the General Manager approves [1]. At Beach Resort, spa cancellations within 12 hours are ch
- **v12** Can guests smoke on the balcony? → No, guests cannot smoke on the balcony. All properties in the group are 100% non-smoking, including balconies and patios [1]. The brand standard also charges a $250 cleaning fee when there is evidence of smoking in a room [1].
- **v13** Do you have an airport shuttle? → Yes, for Miami International Airport (MIA), the hotel offers pickups: a sedan for $65 one way (up to 3 guests) or an SUV for $95 one way (up to 6 guests), booked at least 24 hours in advance [1]. The hotel does not offer transfers from Fort Lauderdale (FLL) and recommends a taxi or rideshare instead
- **v14** Where can I leave my luggage after checkout? → You can leave luggage at the front desk, where it is tagged and kept in a locked room behind the desk, free of charge, but only on the same day as check-out. Bags cannot be stored overnight after check-out [1].
- **v15** Is there a laundry service? → Yes. Same-day valet laundry and dry cleaning is available if items are dropped at the front desk by 9:00 AM for return by 6:00 PM. Prices are on the laundry card in the room, and there is no self-service laundry room [1].
- **v16** What are the quiet hours? → Quiet hours are 11:00 PM to 7:00 AM [1].
- **v17** Do you have accessible rooms? → Yes. The brand-wide handbook says every property has accessible rooms with roll-in showers, grab bars, and lowered closet rails, and visual alarm and doorbell kits are available on request [1]. Guests should ask for one when booking, and the front desk confirms it at check-in [1]. The documents don'
- **v18** How does the loyalty program work? → Members earn 10 points per US dollar spent on the room rate, but taxes, resort fees and pet fees don't earn points [2]. Tiers are based on nights per year: Silver (5+), Gold (15+) and Platinum (40+), each with increasing late check-out, welcome amenity and room upgrade benefits [4]. Always confirm t
- **v19** What does the resort fee include? → The Beach Resort fee is $35 per night plus tax and includes Wi-Fi, bike rental and two bottles of water per day [1]. Wi-Fi coverage extends to all rooms, the rooftop pool and the beach chair area [2].
- **v20** What are the spa hours? → The Beach Resort spa is open 9:00 AM to 8:00 PM daily [1].
- **v21** Is there Wi-Fi? → Yes, Wi-Fi is free for all guests, with no resort fee. The network is MountainLodge-Guest, and the password is printed on the key card sleeve [1]. The signal is weaker in the cabins, so a free range extender is available at the front desk [1].
- **v22** What time is checkout? → Standard check-out is 11:00 AM [1]. Late check-out is subject to availability, and non-loyalty guests can request it until 1:00 PM for a $30 fee [3]. Loyalty members get late check-out based on tier [5], and individual properties may set stricter limits [3]. No Mountain Lodge-specific policy was pro
- **v23** Is breakfast included? → Yes, a continental breakfast is included in every room rate and is served from 7:00 AM to 10:00 AM in the Great Room [1].
- **v24** Is there a pool? → Mountain Lodge does not have an on-site pool. Guests get free day passes to a partner fitness center 0.5 miles away, which has an indoor pool [2].
- **v25** Is there a gym? → Mountain Lodge doesn't mention an on-site gym. Guests get free day passes to a partner fitness center 0.5 miles away, which has an indoor pool [3]. Please check with a manager whether any on-site fitness facilities exist.
- **v26** Can I bring my dog? → Yes, dogs of any size are welcome at Mountain Lodge, with a maximum of 2 per room [1]. A pet fee of $50 per night per room applies, capped at $200 per stay [1]. Cats and other pets are not permitted [1].
- **v27** Is parking free? → Yes, self-parking at Mountain Lodge is free [1]. RVs and trailers must use the overflow lot, and guests can ask the front desk for directions [1].
- **v28** What are the quiet hours? → Quiet hours at Mountain Lodge are 10:00 PM to 7:00 AM [1].
- **v29** Do you have an airport shuttle? → Yes. The shuttle goes to and from Asheville Regional Airport (AVL) for $35 per person one way, runs hourly on the hour from 7:00 AM to 9:00 PM, and must be booked at least 12 hours ahead [1].
- **v30** Can I check in early? → Early check-in isn't guaranteed and depends on whether rooms are ready [1]. At Mountain Lodge, early check-in before 12 PM costs $25 if a room is ready, and it isn't offered on October weekends because of wedding blocks [2]. Standard check-in is 3:00 PM, and you should not promise early check-in at 
- **v31** Is there a laundry room? → Yes. Mountain Lodge has a guest coin laundry on the ground floor, open 7:00 AM to 10:00 PM [1]. Detergent pods are $2 at the front desk [1].
- **v32** Can we host a wedding here? → The sources show Mountain Lodge has a garden lawn for up to 150 guests and an indoor event room for up to 60 [2]. Event dates are confirmed with a 30% non-refundable deposit, and weddings need a minimum block of 10 rooms, released 30 days before arrival [2]. The sources don't confirm whether a speci
- **v33** I left something in my room. What happens to it? → Items left in rooms are logged in the Lost & Found binder and kept for 90 days [1]. If the item is shipped to the guest, the guest pays the shipping cost, and staff must not ship anything without a confirmed address from the guest's own email [1]. The sources don't say how a guest can pick up an ite
- **v34** How do I earn loyalty points? → Members earn 10 points per US dollar spent on the room rate. Taxes, resort fees, and pet fees do not earn points [1]. Guests who opt out of daily housekeeping earn 250 Guest Rewards points per night [2].
- **v35** Are there hiking trails nearby? → Yes. The Ridge Loop trail (3 miles) starts behind the lodge, and free trail maps are available at the front desk [1]. Guided hikes run Saturdays at 9:00 AM for $20 per person, and you can book at the front desk by Friday evening [1].
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
