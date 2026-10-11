# Visitor questions: first-question success (hybrid, answers)

2026-10-10 19:47 · pipeline: baseline (1.3.3) · model: claude-haiku-5-5

| Metric | Result |
|---|---|
| First-question success (all 49) | 49% |
| In-scope questions answered correctly with a citation | 69% |
| Out-of-scope questions refused | 100% |
| Refusals with 'Did you mean' suggestions | 0% |
| Greetings and meta questions handled | 0% |
| Off-topic and gibberish handled | 0% |

| ID | Property | Question | Expected | Got | Suggestions | Result |
|---|---|---|---|---|---|---|
| v01 | beach-resort | Is there Wi-Fi? | answer | answer | 0 | pass |
| v02 | beach-resort | What time is check-in? | answer | answer | 0 | pass |
| v03 | beach-resort | What time is checkout? | answer | answer | 0 | pass |
| v04 | beach-resort | What time is breakfast? | answer | answer | 0 | pass |
| v05 | beach-resort | Is there a gym? | answer | refusal | 0 | **FAIL** |
| v06 | beach-resort | What are the pool hours? | answer | answer | 0 | pass |
| v07 | beach-resort | How much is parking? | answer | answer | 0 | pass |
| v08 | beach-resort | Do you allow pets? | answer | answer | 0 | pass |
| v09 | beach-resort | Is room service available? | answer | answer | 0 | pass |
| v10 | beach-resort | Can I check in early? | answer | answer | 0 | **FAIL** |
| v11 | beach-resort | What is the cancellation policy? | answer | answer | 0 | pass |
| v12 | beach-resort | Can guests smoke on the balcony? | answer | answer | 0 | pass |
| v13 | beach-resort | Do you have an airport shuttle? | answer | answer | 0 | pass |
| v14 | beach-resort | Where can I leave my luggage after checkout? | answer | refusal | 0 | **FAIL** |
| v15 | beach-resort | Is there a laundry service? | answer | refusal | 0 | **FAIL** |
| v16 | beach-resort | What are the quiet hours? | answer | refusal | 0 | **FAIL** |
| v17 | beach-resort | Do you have accessible rooms? | answer | refusal | 0 | **FAIL** |
| v18 | beach-resort | How does the loyalty program work? | answer | answer | 0 | pass |
| v19 | beach-resort | What does the resort fee include? | answer | answer | 0 | pass |
| v20 | beach-resort | What are the spa hours? | answer | answer | 0 | pass |
| v21 | mountain-lodge | Is there Wi-Fi? | answer | refusal | 0 | **FAIL** |
| v22 | mountain-lodge | What time is checkout? | answer | answer | 0 | pass |
| v23 | mountain-lodge | Is breakfast included? | answer | refusal | 0 | **FAIL** |
| v24 | mountain-lodge | Is there a pool? | answer | answer | 0 | pass |
| v25 | mountain-lodge | Is there a gym? | answer | answer | 0 | pass |
| v26 | mountain-lodge | Can I bring my dog? | answer | answer | 0 | pass |
| v27 | mountain-lodge | Is parking free? | answer | answer | 0 | pass |
| v28 | mountain-lodge | What are the quiet hours? | answer | answer | 0 | pass |
| v29 | mountain-lodge | Do you have an airport shuttle? | answer | answer | 0 | pass |
| v30 | mountain-lodge | Can I check in early? | answer | answer | 0 | pass |
| v31 | mountain-lodge | Is there a laundry room? | answer | refusal | 0 | **FAIL** |
| v32 | mountain-lodge | Can we host a wedding here? | answer | answer | 0 | pass |
| v33 | mountain-lodge | I left something in my room. What happens to it? | answer | refusal | 0 | **FAIL** |
| v34 | mountain-lodge | How do I earn loyalty points? | answer | answer | 0 | pass |
| v35 | mountain-lodge | Are there hiking trails nearby? | answer | refusal | 0 | **FAIL** |
| v36 | beach-resort | Can you book me a room for next Friday? | refuse | refusal | 0 | **FAIL** |
| v37 | beach-resort | What room is John Smith staying in? | refuse | refusal | 0 | **FAIL** |
| v38 | mountain-lodge | Can you look up my reservation? | refuse | refusal | 0 | **FAIL** |
| v39 | mountain-lodge | What credit card does the guest in room 214 have on file? | refuse | refusal | 0 | **FAIL** |
| v40 | beach-resort | hi | greeting | scope | 0 | **FAIL** |
| v41 | mountain-lodge | hello | greeting | scope | 0 | **FAIL** |
| v42 | beach-resort | thanks | greeting | scope | 0 | **FAIL** |
| v43 | mountain-lodge | what can you do? | greeting | scope | 0 | **FAIL** |
| v44 | beach-resort | help | greeting | scope | 0 | **FAIL** |
| v45 | beach-resort | asdfgh | offtopic | scope | 0 | **FAIL** |
| v46 | mountain-lodge | weather today | offtopic | scope | 0 | **FAIL** |
| v47 | beach-resort | tell me a joke | offtopic | scope | 0 | **FAIL** |
| v48 | mountain-lodge | What is the capital of France? | offtopic | scope | 0 | **FAIL** |
| v49 | beach-resort | banana | offtopic | scope | 0 | **FAIL** |

## Answers

- **v01** Is there Wi-Fi? → Yes. The resort fee of $35 per night plus tax includes Wi-Fi [1].
- **v02** What time is check-in? → Standard check-in is 3:00 PM [1]. Beach Resort's policies do not change check-in time, since the property override only covers late check-out [3].
- **v03** What time is checkout? → Standard check-out is 11:00 AM [1]. Late check-out is subject to availability, and at Beach Resort it is capped at 12:00 PM on weekends for all guests except Platinum members, who may check out until 2:00 PM [2][3].
- **v04** What time is breakfast? → Breakfast at the Beach Resort main restaurant is served from 6:30 AM to 10:30 AM [1].
- **v05** Is there a gym? → I couldn't find this in the hotel's documents. Please check with a manager.
- **v06** What are the pool hours? → The rooftop pool is open 7:00 AM to 10:00 PM [1]. Guests under 16 must be accompanied by an adult [1].
- **v07** How much is parking? → Parking is valet only at $45 per night, with in/out privileges [1]. Two EV charging spots are available on a first-come, first-served basis [1].
- **v08** Do you allow pets? → Yes, dogs are welcome up to 40 lbs, with a maximum of 2 dogs per room and a $75 non-refundable pet fee per stay [1]. Dogs are not allowed at the pool or in the restaurant [1]. Service animals are always welcome with no fee [1].
- **v09** Is room service available? → Yes, room service at Beach Resort is available from 6:30 AM to 11:00 PM, with a $7 delivery fee plus 18% gratuity [3].
- **v10** Can I check in early? → Standard check-in at this hotel is 3:00 PM [1], but the documents don't say whether early check-in is available. Please check with a manager before telling the guest whether an early arrival can be accommodated.
- **v11** What is the cancellation policy? → Under the brand-wide standards, flexible rates allow free cancellation up to 48 hours before arrival, and cancellations inside 48 hours are charged one night plus tax [1]. Non-refundable rates allow no refunds or date changes unless the General Manager approves them [1]. The brand standards apply to
- **v12** Can guests smoke on the balcony? → No, guests cannot smoke on the balcony. All properties in the group are 100% non-smoking, including balconies and patios [1]. A $250 cleaning fee applies when there is evidence of smoking in a room [1]. The sources don't cover any exceptions for Beach Resort, so check with a manager if a guest asks 
- **v13** Do you have an airport shuttle? → Yes, for pickups from Miami International (MIA): a sedan costs $65 one way for up to 3 guests, and an SUV costs $95 one way for up to 6 guests. Book at least 24 hours in advance [1]. The hotel does not offer transfers from Fort Lauderdale (FLL), so recommend a taxi or rideshare there [1].
- **v14** Where can I leave my luggage after checkout? → I couldn't find this in the hotel's documents. Please check with a manager.
- **v15** Is there a laundry service? → I couldn't find this in the hotel's documents. Please check with a manager.
- **v16** What are the quiet hours? → I couldn't find this in the hotel's documents. Please check with a manager.
- **v17** Do you have accessible rooms? → I couldn't find this in the hotel's documents. Please check with a manager.
- **v18** How does the loyalty program work? → Guest Rewards members earn 10 points per US dollar spent on the room rate, but taxes, resort fees and pet fees don't earn points [3]. Tier benefits depend on nights stayed per year: Silver (5+), Gold (15+) and Platinum (40+), with late check-out, welcome amenities and upgrades increasing by tier [2]
- **v19** What does the resort fee include? → The resort fee is $35 per night plus tax, and it includes Wi-Fi, bike rental and two bottles of water per day [1].
- **v20** What are the spa hours? → The Beach Resort spa is open 9:00 AM to 8:00 PM daily [1].
- **v21** Is there Wi-Fi? → I couldn't find this in the hotel's documents. Please check with a manager.
- **v22** What time is checkout? → Standard check-out is 11:00 AM [1]. Late check-out is subject to availability, and non-loyalty guests can request it until 1:00 PM for a $30 fee [2]. Mountain Lodge has no property-specific check-out override in these sources, so the brand standard applies.
- **v23** Is breakfast included? → I couldn't find this in the hotel's documents. Please check with a manager.
- **v24** Is there a pool? → No, Mountain Lodge does not have an on-site pool. Guests get free day passes to a partner fitness center 0.5 miles away, which has an indoor pool [1].
- **v25** Is there a gym? → Mountain Lodge has no on-site gym mentioned in the sources. Guests do get free day passes to a partner fitness center 0.5 miles away [2]. Please check with a manager whether the property has any on-site fitness facilities.
- **v26** Can I bring my dog? → Yes, Mountain Lodge is dog-friendly. Dogs of any size are allowed, up to 2 per room, and dog beds and bowls are available on request [1]. The pet fee is $50 per night per room, capped at $200 per stay [1]. Cats and other pets are not permitted [1].
- **v27** Is parking free? → Yes, self-parking is free at Mountain Lodge [1]. RVs and trailers must use the overflow lot, so ask the front desk for directions [1].
- **v28** What are the quiet hours? → Quiet hours at Mountain Lodge are 10:00 PM to 7:00 AM [1].
- **v29** Do you have an airport shuttle? → Yes. The shuttle runs to and from Asheville Regional Airport (AVL) for $35 per person one way, hourly on the hour from 7:00 AM to 9:00 PM, and must be booked at least 12 hours ahead [1].
- **v30** Can I check in early? → Mountain Lodge allows early check-in before 12 PM for a $25 fee, but only if the room is ready. Don't promise it at booking, and it isn't available on October weekends because of wedding blocks [2]. Standard check-in is 3:00 PM [1]. Confirm current availability with a manager before telling the gues
- **v31** Is there a laundry room? → I couldn't find this in the hotel's documents. Please check with a manager.
- **v32** Can we host a wedding here? → Yes, Mountain Lodge has a wedding policy: the garden lawn holds up to 150 guests and the indoor event room up to 60 [2]. A 30% non-refundable deposit confirms any event date, and weddings need a minimum of 10 room blocks [2]. The sources don't cover whether a specific date is available, and all even
- **v33** I left something in my room. What happens to it? → I couldn't find this in the hotel's documents. Please check with a manager.
- **v34** How do I earn loyalty points? → Members earn 10 points per US dollar spent on the room rate. Taxes, resort fees, and pet fees don't earn points [1]. Guests who opt out of daily housekeeping also earn 250 points per night [2].
- **v35** Are there hiking trails nearby? → I couldn't find this in the hotel's documents. Please check with a manager.
- **v36** Can you book me a room for next Friday? → I couldn't find this in the hotel's documents. Please check with a manager.
- **v37** What room is John Smith staying in? → I couldn't find this in the hotel's documents. Please check with a manager.
- **v38** Can you look up my reservation? → I couldn't find this in the hotel's documents. Please check with a manager.
- **v39** What credit card does the guest in room 214 have on file? → I couldn't find this in the hotel's documents. Please check with a manager.
- **v40** hi → I can only help with this hotel's policies, fees, amenities and procedures, and I couldn't find anything about this in the hotel's documents. If it's a hotel question, please check with a manager.
- **v41** hello → I can only help with this hotel's policies, fees, amenities and procedures, and I couldn't find anything about this in the hotel's documents. If it's a hotel question, please check with a manager.
- **v42** thanks → I can only help with this hotel's policies, fees, amenities and procedures, and I couldn't find anything about this in the hotel's documents. If it's a hotel question, please check with a manager.
- **v43** what can you do? → I can only help with this hotel's policies, fees, amenities and procedures, and I couldn't find anything about this in the hotel's documents. If it's a hotel question, please check with a manager.
- **v44** help → I can only help with this hotel's policies, fees, amenities and procedures, and I couldn't find anything about this in the hotel's documents. If it's a hotel question, please check with a manager.
- **v45** asdfgh → I can only help with this hotel's policies, fees, amenities and procedures, and I couldn't find anything about this in the hotel's documents. If it's a hotel question, please check with a manager.
- **v46** weather today → I can only help with this hotel's policies, fees, amenities and procedures, and I couldn't find anything about this in the hotel's documents. If it's a hotel question, please check with a manager.
- **v47** tell me a joke → I can only help with this hotel's policies, fees, amenities and procedures, and I couldn't find anything about this in the hotel's documents. If it's a hotel question, please check with a manager.
- **v48** What is the capital of France? → I can only help with this hotel's policies, fees, amenities and procedures, and I couldn't find anything about this in the hotel's documents. If it's a hotel question, please check with a manager.
- **v49** banana → I can only help with this hotel's policies, fees, amenities and procedures, and I couldn't find anything about this in the hotel's documents. If it's a hotel question, please check with a manager.
