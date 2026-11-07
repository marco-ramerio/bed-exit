# Bed Exit Detection — Build Plan

*The only build document. The review and the open questions have both been folded in. Nothing is waiting on an answer.*

## What this is

A camera watches the bed. When it sees her getting up, it synthesises a press of the ChunHee call button she already has, and the existing plug-in receivers ring in other people's rooms. Nothing downstream changes: same pager, same receivers, same wall sockets. The camera simply replaces her finger on the button, because she no longer remembers to press it.

Detection is pose estimation, not a vision language model. A VLM on a Pi takes over two minutes per frame; pose estimation runs at 6 to 12 frames per second on the same board. The trigger is a geometric test on skeleton keypoints, which makes it deterministic, testable, and tunable by changing numbers rather than prompts.

## What this is not

**Not a safety system, and it must never be described to the family as one.** The actual coverage is her husband, who sleeps a few metres away and hears her move. That was true before this project and stays true after it. The camera is an extra, and it stays an extra until it has earned otherwise over months of real nights.

The risk this rule now guards against is not a missing sensor. It is that he starts sleeping through, on the strength of a box he has been told rings, before it has earned that. He will not announce the night he does. So the rule has a matching action: before the rig goes on her table, tell him plainly what it does and does not do, and keep telling him while it is still young.

**It is also, openly, a learning project.** Building it is a goal in its own right: hands on pose estimation, embedded Linux, GPIO and RF. That is a legitimate reason to build something, and naming it is what keeps it honest. It is not the reason to trust it, and it is why the paragraph above is a rule rather than a caveat.

Silent failure is the reason. WiFi drops, SD cards corrupt, cameras hang, mounts get knocked in the dark. A system that fails quietly is worse than no system if anyone has started relying on it.

---

## The existing ChunHee system

What you already own, and what it means for the RF work in step 6.

| Fact | Consequence |
|---|---|
| Frequency not printed on the unit | 433.92MHz is what the ChunHee range uses and is near-certain for a EU-market kit, but it is unconfirmed. Buy both a 433.92MHz and a 315MHz module pair. They are about €4 each, and owning both turns a two-week shipping delay into a five-minute swap. |
| Learning code, not rolling code | The transmitter sends the same code every press, so it can be captured and replayed. This is the assumption the whole RF route rests on, and step 6 verifies it in five minutes at your kitchen table before anything else is built. |
| Each receiver pairs with up to 50 buttons | A spare transmitter can be added without touching hers. |
| 55 ringtones, assignable per button | The automated trigger gets its own melody as a hardware feature. Nothing to build. |
| Volume adjustable, 5 levels to 115dB | Per-receiver, so different rooms can ring at different volumes. |
| Receivers are in other people's rooms, not hers | The alarm is a signal to whoever is on call. It is not an event in her room, so it cannot startle her into moving faster. |

---

## Decisions taken

Settled, so they do not get relitigated at 1am halfway through a build.

**A camera in her room is agreed.** Marco holds the decision and has taken it. The design writes short clips only around fire events and never records continuously, and that stays true.

**The 850nm illuminator's red glow is acceptable.** No need for 940nm. Buy the cheap one, but see *Physical build* for the spec: 5V USB, wide beam, bounced off the wall rather than aimed at her.

**One trigger, one outcome.** No two-tier alarm, no quiet early warning. The receivers ring or they do not.

**Bias toward false alarms.** A ring when nothing happened is the acceptable failure. A missed exit is not. This drives threshold choice in step 3 and is written up there.

**Build it anyway, knowingly.** The camera route is not the easiest way to detect a bed exit. It is the chosen way, because building it is part of the point. The alternatives were researched and rejected on their merits, below.

**No commercial sensor is being bought alongside this.** Decided 22 August 2026, reversing the earlier plan. See *Routes considered and rejected* for the reasoning and for the one argument that does **not** support it.

---

## Routes considered and rejected

Researched properly before committing. Recorded so none of it gets rediscovered later.

**PIR bed exit sensor — considered, then dropped on 22 August 2026.** A passive infrared sensor mounted low at the side of the bed, aimed at where feet land, ringing a plug-in receiver. Roughly €35 to €50, factory paired, working in ten minutes. Earlier versions of this document carried it as the coverage layer and told you to buy it immediately.

**Dropped because the coverage already exists.** Her husband sleeps a few metres away and checks on her. A beeper on a bedside table is not an improvement on a person in earshot, and another box in the flat has its own cost. That is the reason, and it is a good one.

**Recorded so it is not re-dropped on the wrong reason.** The objection raised at the time was the mattress: one mattress, an anti-decubitus airbag inflating and deflating on a cycle, and cushion wedges under her back and legs. That objection is real, and it is fatal to a **pressure pad** and to **mmWave**, both of which are rejected below for exactly it. It does not touch a PIR. Passive infrared reads body heat moving through a cone of air beside the bed; it never contacts the mattress, and inflation cycles emit no heat motion. PIR is what survived the mattress, not what failed it. If this decision is ever revisited, revisit it on the husband, not on the airbag.

Two things that would have applied had it been bought, kept for the day it is: it may pair straight to a ChunHee receiver already in the flat, since both are 433.92MHz plug-in systems with five volume levels and selectable ringtones, which is the EV1527 signature. And a wireless PIR runs on batteries, so it fails silently when they go, which needs a fixed date in the calendar rather than good intentions.

**Load cells under the bed legs — rejected.** Four 50kg cells and an HX711 is a cheap, well-documented build that would be immune to the air mattress, since air moves inside the mattress but total mass does not change. Rejected for two reasons. Weight only leaves the bed once she is already up or already going down, which is later than a torso-based trigger and arguably too late to be worth building. And at 52kg her signal is small against the mass of bed, mattress and bedding, so the detection margin is thin exactly where it needs to be reliable.

**mmWave radar — rejected for this bed specifically.** An LD2410 or LD2450 with an ESP32 is about €20, sees through a duvet, works in complete darkness, and involves no camera. In most bedrooms it would be the obvious answer. Not this one: mmWave identifies a still person by breathing micro-motion, and is well known for being fooled by any moving object. An alternating-pressure mattress inflates and deflates continuously, by design, in the exact detection zone. The likely outcome is a bed that reads occupied permanently and never registers an exit. This is a reasoned prediction rather than a tested result, and it would cost about €15 to disprove if anyone wants to.

**What the research says about the chosen route.** In-bed pose estimation under blankets is an open research problem with its own review literature, and the methods that work are multimodal, fusing depth, infrared and pressure, because RGB or IR alone does not survive the covers. One 2025 paper improved real blanket-occluded accuracy by 2.3% PCK, which indicates how hard the remaining ground is. Two findings support the design here: nano-scale YOLO pose models are the accuracy-efficiency sweet spot, and keypoint confidence degrades into diffuse low-confidence peaks under occlusion, which is precisely what the confidence gating in step 3 exploits. Go in expecting step 2 to be genuinely uncertain.

---

## Physical build

Decided August 2026, once the camera position was fixed. Drawn to scale: [The Bedside Rig](https://claude.ai/code/artifact/9b4c2af1-289b-4e94-9819-3f88d08d3842).

**Where it goes.** A fixed bedside table on the side she does *not* get out of, camera at about 1m, shooting across the bed. Table top ~0.90m, lens ~1.00m.

This position is better than the wall mount originally assumed. A near-level side-on view is the best possible angle for measuring torso rotation, which is the primary feature. Two consequences follow:

- **The ankle test contributes nothing, and this is now measured rather than predicted.** The 21 August calibration killed it outright: her ankles read *further* from the camera axis while lying than while sitting or standing, so no bed-edge value separates the two. `ANKLE_TEST` is `False`. Torso angle carries the detector alone. The reserve feature is hip-midpoint height, and it stays unbuilt until real overnight data asks for it.
- **Hardcoded pixel geometry is legitimate.** The table does not move. `BED_EDGE_X` was the original case and is now unused; `BED_BOX`, which decides *which person in frame is her*, is the one that matters and is set the same way, off a still at the deployment geometry.

**Lens: Camera Module 3 Wide NoIR, not standard.** Still a correctness requirement rather than an upgrade, but the reason changed on 22 August 2026 and the old one no longer holds.

The original argument was vertical: the standard module is 41° vertical, which at ~1m bottoms out 0.37m above the floor and never sees her feet. That argument died with the ankle test. Feet in frame is no longer a requirement at all.

The argument that replaces it is horizontal, and it is stronger. The standard module is 66° horizontal, which at 1m covers about 1.30m across. A person lying side-on is longer than that, so a standard lens cannot hold her shoulders and hips in the same frame from a bedside table, and shoulders-to-hips *is* the feature. Wide, at 102°, covers about 2.47m and holds the whole body with room either side.

One useful consequence: since floor coverage no longer matters, the exact height of the table stopped being a sensitive number. Anywhere from about 0.80m to 1.00m is fine, and the mount can be set by eye against the live confidence readout rather than measured.

**Case: Waveshare aluminium with integrated blower.** It cools the board itself, so the Active Cooler is not needed and does not fit alongside it.

The catch: **aluminium is a Faraday cage.** The FS1000A must not live inside it. It gets its own small plastic box sitting beside the Pi case, holding the breadboard and the module, with the antenna wire straight and vertical. A transmitter inside metal works on the bench with the lid off and fails silently once closed, which is exactly the failure mode this document opens by warning about.

**Camera outside the case, in its own camera case on a mini ball head.** The 500mm ribbon exists so the camera can be re-aimed without moving the Pi, and the ball head is what makes that a five-second job rather than an evening of folded-paper shims.

Keep the camera off the radio box. That box should sit still forever with a vertical antenna, while the camera gets adjusted repeatedly, and coupling them means every re-aim tilts the antenna and flexes the ribbon connector. Tape the ribbon where it leaves the case; it fails by working loose, not by snapping.

**Power: the official 27W supply feeds the Pi and everything the Pi carries.** Case fan via the 4-pin header, camera via the CSI ribbon, transmitter via GPIO.

This only works with the official supply. The Pi 5 negotiates for 5.1V/5A, and a normal GaN phone charger caps its 5V rail at 3A, which silently drops the USB peripheral budget from 1.6A to 600mA. **Never feed the Pi from a 12V brick through a buck converter:** undervoltage is the SD-corrupting failure named under the night run.

**The illuminator is the exception, and it runs on its own supply.** Two wall plugs, not one. Revised 21 August 2026, see below.

**Illuminator: 850nm, 3–5W, 90° beam, on its own mains adapter.** The spec that matters is power and beam width. Voltage is a rail spec, not a brightness spec, and the original "5V USB" line conflated the two.

The optical argument stands and is the one to obey: 12V CCTV floodlights are built to throw 20–50m at 25–30fps, and here the subject is at 1m and the camera runs at 5fps, so each frame can expose five times longer. A 12W spotlight at one metre overexposes skin to flat white, destroying the contrast the pose model needs just as effectively as darkness. **So reject them for being too powerful and too narrow, not for being 12V.** A 3–5W board at 90° is a modest, wide source whatever rail it runs on.

The electrical argument, by contrast, only ever applied to 12V *touching the Pi*. A separate adapter into its own socket shares no rail, no converter and no ground with the Pi, so there is no undervoltage path and nothing to protect against.

**The rule that replaces it:** the illuminator side shares nothing with the Pi. Not power, not ground, not a connector. Two independent devices in one room. If a wire ever runs between them, stop.

Nothing is lost. The Pi never switched the illuminator anyway; it runs continuously, which is why the photoresistor below is a nuisance rather than a feature.

**Why this was revised.** The 5V USB variant is genuinely scarce in Europe. Amazon in it, de and es stocks only 12V CCTV units and battery torches; the 5V boards live on AliExpress and eBay at three weeks' transit for a €2 part. With the first child due 29 August 2026 and evenings in that room the scarce resource, spending three weeks of lead time to save one wall plug is the wrong trade. Next-day from Amazon.it takes the last long-lead item off the critical path.

Aim it at the wall behind the camera at roughly 45° rather than at the ceiling. Bouncing costs a factor of five to ten, and the wall is a much shorter path than the ceiling while still keeping the source out of her eyeline.

**Camera-mounted illuminator boards: considered 22 August 2026, rejected.** The common advice for Pi night vision is a 3W 850nm board that bolts onto the camera PCB, runs off the Pi's 5V and auto-switches on a built-in photoresistor. It is good advice for a camera watching a room from three metres. It is wrong at one metre, on all four counts, and each one matters here:

- It cannot be bounced, so it lights her face directly at 1m and flattens the contrast the pose model needs. The bounce is the mechanism, not a preference.
- The 3W versions want a heat sink, and bolting a heater to the image sensor raises noise in exactly the low-light conditions you are trying to survive.
- 600mA off the Pi's 5V rail reintroduces the undervoltage path that the separate-supply rule exists to remove.
- The photoresistor oscillates across dawn, which is inside the night run.

Also rejected on the same date: the Arducam Day-Night module, which bundles NoIR and IR LEDs and would remove the guesswork, but is not a 102° wide lens and therefore cannot hold shoulders and hips in one frame from a bedside table.

Watch for the built-in photoresistor most of these ship with. The night run spans dawn, and a sensor hunting around its threshold will oscillate scene brightness between 06:00 and 07:00. If confidence collapses in that window, look here before blaming the model.

---

## Shopping list

**For steps 1 to 3: nothing.** Your existing laptop and webcam are sufficient. Do not buy anything until step 2 confirms that pose estimation actually tracks her in bed.

This is an MVP list. It buys one working path, not a spare for every failure. When something breaks, diagnose it and buy the fix then — see *If it breaks* below.

Sourced 20 August 2026, shipping to Milan, buying anywhere in the EU. Prices below are as checked on that date and the Pi ones in particular will move.

### Why the board costs what it does

Kept because it is the reason 2GB was refused, and because the price will look absurd later.

**The Pi 5 roughly doubled in price during the DRAM shortage.** Two increases in three months, and the 8GB took a $50 rise in April 2026 on top of the December 2025 one. Checked across Europe on 20 August: BerryBase €184.90, Welectron €189.00, Melopero €190.02, heise price comparison bottoming out at €184.90. Four sellers in three countries agreeing within €6 is not reseller markup. That is the board price now.

**4GB was the right size and 8GB is what got bought, because the 4GB was not purchasable.** On 22 August it was out of stock at Melopero and at Botland, whose restock estimate was 13 November, and Farnell Italia was quoting delivery from 16 September. So the €66 question never had to be argued to a conclusion.

The reasoning that matters for sizing is what the software holds in memory, and it is not the model.

YOLO11n-pose is a few megabytes on disk, so the tempting conclusion is that 2GB is plenty. That is wrong, because `ultralytics` imports PyTorch at package import time whether or not you are running NCNN inference, and PyTorch on ARM64 is most of the footprint. The measured figure from someone running exactly this stack, YOLO11n via NCNN on a Pi 5, is that memory never went above 1GB. Add Raspberry Pi OS, the CMA region libcamera reserves for camera buffers, OpenCV, and the clip encoder, and a realistic working set is 1.2 to 1.4GB.

On a 2GB board that leaves a few hundred megabytes of headroom. It would probably run. But "probably runs" is the wrong standard for a process that has to survive a week of unattended nights in someone else's bedroom, and the way it fails is by swapping onto the microSD, which is the same card the *Two things that will bite* section already warns about corrupting. Saving €62 by putting the detector 300MB from the ceiling is a bad trade on a system whose entire opening warning is about dying quietly at 01:30.

4GB is the size where the workload fits with room to spare and you stop thinking about it, and 8GB is comfortably past that. The extra memory buys reuse after the project, not headroom the detector needs, and should not get re-argued later as though the workload demanded it.

### Suppliers

Buying across the EU collapses this to two orders, and one of them is small.

**[BerryBase](https://www.berrybase.de/en/)** — German, Mainz, ships across the EU, and the single most useful find in this whole exercise. They carry the Raspberry Pi first-party parts *and* the loose components, which no Italian seller does. Twelve of the fifteen lines came from here in one order, including the FS1000A that Melopero does not stock at all, and shipping to Italy turned out to be free. Their site runs in English and Italian.

**[Amazon.it](https://www.amazon.it/)** — the remaining three lines: the IR illuminator and the 315MHz pair, which BerryBase does not carry, and the Dupont set, which it carries but had out of stock. Earlier drafts listed ChunHee spares and a PIR sensor here as well. Both are gone; do not re-add them from memory.

**Melopero is now the fallback rather than the plan.** They are still the right answer if something goes wrong mid-build and you need it in Italy by Wednesday, since they are in Rome and ship 24/48h. But BerryBase beats them on nearly every line: camera €36.50 against €38.00, microSD €19.50 against €31.49, and the 2GB board €55 against €70.58. Worth knowing their banner currently says orders ship Mondays, so treat Melopero as a weekly dispatch if you do fall back to them.

### The order as placed, 23 August 2026

BerryBase went in on the morning of 23 August. Amazon is basketed and deliberately deferred; see the note under order 2. Prices are what was paid or basketed, not estimates. Product numbers are included because BerryBase lists near-identical variants and the numbers are unambiguous.

**Order 1 — BerryBase, twelve lines, shipping free, delivery 23–25 August**

| Item | Product no. | Paid |
|---|---|---|
| Raspberry Pi 5, 8GB | RPI5-8GB | €184.90 |
| Official 27W USB-C supply, black | RPI5NT5AB | €12.40 |
| Armor case with fan, black | RPI5-ARC-FA | €13.90 |
| Camera Module 3 **Wide NoIR**, 12MP | RPI-CAM3-WN | €36.50 |
| Camera mount, 1/4" tripod thread, incl. mini tripod | RPI-CAM-MO | €3.90 |
| Camera cable, Standard–Mini, 500mm | RPI-CC-SM-50 | €3.50 |
| FS1000A 433MHz TX/RX pair | FS1000A | €1.90 |
| Mini breadboard, 170 contacts, red | BB-170P-RED | €0.99 |
| Plastic housing, 72×50×28mm | E-KG28M | €2.50 |
| Copper switching wire, insulated, ø0.5mm, 10m, black | E105-1 | €1.90 |
| 525-piece metal film resistor assortment | RESKIT-5 | €7.90 |
| [SanDisk Extreme microSDXC A2 U3 V30 170MB/s 64GB + adapter](https://www.berrybase.de/en/sandisk-extreme-microsdxc-a2-uhs-i-u3-v30-170mb-s-memory-card-adapter-64gb/) | 619659188566 | €25.90 |

**Twelve lines, €296.19.** With the 200MB/s Extreme Pro the cart stood at €300.49; the plain Extreme was swapped in at the last moment, saving €4.30, because nothing in this build touches sequential throughput. A2 is the spec that matters and both carry it.

**Shipping to Italy was free**, against a budgeted €10–20.

**Order 2 — Amazon.it, three lines, €57.77, not yet placed**

| Item | Paid |
|---|---|
| [Lonnky 8-LED 850nm, 90°, 12V 1A PSU included](https://www.amazon.it/Illuminatore-grandangolare-Lonnky-inondazione-infrarossa/dp/B07STM1L96) | €31.29 |
| [Kit 120 Jumper Wire, Dupont 3-in-1, 20cm](https://www.amazon.it/Breadboard-Maschio-Femmina-Maschio-Maschio-Femmina-Femmina-Raspberry/dp/B0DSDV4YK1) | €14.99 |
| Hailege 5pc 315MHz TX/RX kit | €11.49 |

**Order the Dupont set and the 315MHz pair together, before the first bench session.** The Dupont gates the RF capture, since the receiver cannot reach the GPIO header without female-to-male jumpers. And the 315MHz pair only earns its price if it is in the box *before* the capture rather than after it; bought late it is a spare rather than the second candidate path, which is the distinction the whole argument for it rests on.

**The illuminator has no deadline.** It is needed at the install visit and nowhere earlier.

### What changed between the plan and the order

Recorded so the gaps between the two documents are deliberate rather than drift.

**The 4GB question closed itself.** It was out of stock across the EU on 22 August: Melopero and Botland both nil, Botland's restock estimated 13 November, Farnell Italia quoting 16 September. The 8GB at €184.90 was the only purchasable board, so the €66 argument never had to be settled. Its extra memory still buys reuse after the project rather than headroom the detector needs.

**Three lines moved to Amazon and one moved back.** BerryBase was out of the official Raspberry Pi microSD and out of every 20cm Dupont set, including the individual F-M and M-M packs. The Dupont stayed on Amazon at €14.99, roughly double the going rate and not worth another hour to fix. The card came back to BerryBase once a SanDisk was found there: €30 against €40.49 on Amazon, but the real reason was the date, since the Amazon seller quoted 27–31 August against 23–25 and the whole bench build sits behind having a card to flash.

**The camera mount was substituted and carries one open question.** RPI-CAM-MO at €3.90 replaced the planned Amazon pairing of camera case plus mini ball head at €14, folding the line into order 1. Verify two things when it arrives: whether it holds the PCB or leaves it bare, and whether the mini tripod gives free-angle aiming or only tilt. The plan wants a ball head specifically so re-aiming is a five-second job, and re-aiming is the one adjustment that happens repeatedly in a room that is hard to get back to. If it is tilt-only, add a €6 ball head then rather than now.

**Two things checked and not bought.** A microSD reader was unnecessary: the MacBook Pro has a card slot and the SanDisk ships with an adapter. And her bedside area needs two free wall sockets, since the Pi and the illuminator share no rail by design. If there is only one, that is a €5 adapter bought locally, not a change to this order.

### Both orders together

| | |
|---|---|
| BerryBase, twelve lines, shipping free, paid 23 Aug | €296.19 |
| Amazon.it, three lines, basketed | €57.77 |
| **Build total** | **€353.96** |

Against a planned ~€330. The €24 overage is entirely the memory card and the Dupont set, both of which came in dearer than estimated, offset by BerryBase shipping to Italy for nothing.

### Deliberately not buying

**AI HAT+ accelerator, €130.** YOLO-pose nano runs fast enough on a bare Pi 5 for this. Do not solve a problem you do not have.

**Official Active Cooler.** Superseded by the aluminium case, and the two do not fit together.

**A soldering iron.** Nothing is blocked on soldering until after the code capture, and an iron is borrowable in Milan. See *The one soldering trip*.

**A UPS HAT.** It would survive an unplug, but it fouls the GPIO header, does not fit the aluminium case, and puts lithium cells in the bedroom of someone who cannot get herself out. The last reason decides it alone.

**Microphone, speaker, screen, VL53L0X.** These belonged to an earlier version of the project and are not needed.

**A PIR bed exit sensor, €35–50.** Dropped 22 August 2026. Not because it would not work, which is the trap: see *Routes considered and rejected* before re-arguing it.

**A physical enable/disable button.** The detector reads a flag file, so the toggle is one line over SSH from anywhere. Do not put a switch in the bedroom.

**ChunHee transmitters or receivers.** Two buttons and two receivers already exist in the flat. See *Order 2*.

---

## Open points to verify during the build

Two lists, because they answer at different moments. Nothing here is a purchase; it is all "look at the thing and confirm what the plan assumed".

This section exists because twice during the order the plan turned out to assert something about a component nobody had checked against the component: power rails on a board that has none, and a 17.3cm antenna in a 72mm box. Both had been sitting in the text for weeks.

### Day one, boxes open

| Check | Why it matters | If it fails |
|---|---|---|
| Does the mini breadboard, with a module and jumpers plugged in, actually **fit inside the 72×50×28mm box**? | Interior height is ~24mm. Board ~8.5mm, module body on top, and vertical Dupont connectors add ~15mm. This is tight and may not close | Lay the jumpers over rather than standing them, or run them out through the antenna hole. Failing that, a taller box, ~€3 |
| Where does the **antenna hole** go, and does the wire stand vertical and clear of the aluminium once drilled? | A 17.3cm antenna does not fit inside the box. It must exit and stand up | Reposition the hole. Free |
| Does the **500mm camera cable** reach from the case to where the mount actually ends up? | The mount position was never measured against the cable | Move the box closer. Free |
| **Fan noise at a metre**, from a sleeping person's position. Note it is a *dual* fan, temperature-controlled, so it will vary through the night | Alarm fatigue and disturbed sleep both kill the project socially rather than technically | Passive aluminium case, ~€20. At 5fps the fins alone are very likely enough |
| Does the **PSU plug** fit her sockets? | German shop, Schuko default | €2 adapter locally |
| Does the assortment actually contain **10kΩ and 20kΩ**? | The 10k is the only thing protecting GPIO 27 | Buy singles locally |

**Already closed, so they do not need re-checking.** The Armor case powers its fans from the Pi's FAN port, not from GPIO, so there is no collision with the transmitter on pins 2, 6 and 11. Its GPIO header stays reachable and the vendor explicitly notes that full ribbon connectors will not fit but Dupont cables will, which is exactly the wiring here. Screws, Allen key and thermal pads are in the box. The camera mount is confirmed suitable.

### First Pi run, before trusting any number

The detector's two load-bearing constants survive the hardware change on their own merits, and that is worth knowing up front. `torso_angle` comes from `atan2(dy, dx)`, and both axes scale identically from the laptop's 1920×1080 to the Pi's 1280×720, so **the angle is invariant under uniform scaling** and `TORSO_UPRIGHT_DEG = 60` ports untouched. `SUSTAIN_SECONDS` is in seconds rather than frames, so it ports too. `BED_EDGE_X` is the one resolution-dependent constant in the file and it is already dead.

What does need checking:

| Check | Why |
|---|---|
| **The camera capture rewrite.** `cv2.VideoCapture(0)` is the V4L2 path and the Camera Module 3 is CSI, via libcamera and picamera2 | `camera_check.py` and the capture half of `calibrate.py` do not run on the Pi as written. Budgeted at an hour in step 4. Everything downstream of `frame` is unchanged |
| **`MIN_CORE_CONF = 0.4` against NCNN output** | It was tuned on PyTorch `.pt` inference. NCNN can return different confidences for the same frame. Compare the distribution before trusting the gate |
| **`MAX_GAP_SECONDS = 1.0` at 5fps** | One second is only five frames. An occasional inference stall produces spurious sustain-window resets that look like missed detections. This is the constant most likely to need raising |
| **Barrel distortion on the 102° Wide lens** | The calibration webcam had nothing like it. A torso near the frame edge can read a distorted angle. Keep her centred |
| **Keypoint confidence under 850nm IR** | The model was trained on RGB daylight and will be fed monochrome IR. Confidence will drop. This is the known project-killer and the week of nights is what answers it |

---

## If it breaks

Nothing here is bought up front. This is a diagnosis-to-fix map, so that when something fails you order one thing rather than rediscovering the problem.

| Symptom | Likely cause | The fix, and roughly what it costs |
|---|---|---|
| Replay works on the bench, receivers do not ring from her room | Antenna twisted rather than soldered, or the module is inside the metal case | Move the module outside the case first, free. Then one soldering trip for a proper 17.3cm antenna |
| Code changes on every button press | Rolling code, not learning code | Optocoupler across a spare transmitter's switch contacts. Breakout module + 30AWG silicone wire + heat-shrink, ~€12, one soldering trip |
| `rpi-rf` errors or transmits nothing on the Pi 5 | The Pi 5's I/O chip broke the `RPi.GPIO` library it depends on | `rpi-lgpio` shim. Free. Check this before assuming the RF hardware is at fault |
| Receiver prints nothing at all during capture | Wrong frequency, or the receiver will not run at 3.3V | Try the 5V-plus-divider wiring first, free and already in the box. If still silent, swap to the 315MHz pair, already bought |
| Card corrupts, Pi will not boot | Undervoltage, or the card filled | Second microSD, €12. Check `vcgencmd get_throttled` returns `0x0` and that the delete-oldest logic is working |
| Skeleton unreliable under the duvet | Occlusion. The known project-killer | Camera angle and IR contrast first, both free. Then fall back to bounding-box height rather than keypoints |
| Fires several times an hour overnight | Thresholds too loose, or a hip the duvet hid and the model invented | Check `hip_conf` in the CSV at the fire timestamps first. Low hips means a geometry fix at the camera; healthy hips means raise `TORSO_UPRIGHT_DEG` or lengthen `SUSTAIN_SECONDS`. Free either way |
| Fires whenever someone is at the bedside | `BED_BOX` unset, or set too generously | Read the box off a fresh still and tighten it. Free, but needs a visit or a remote frame grab |
| Nothing is ever detected, `NO PERSON IN BED` on every frame | `BED_BOX` set too tight, or the camera was knocked | Compare against the reference still, then widen the box. Free |
| Frame looks different from last week | The ball head was knocked. The table is fixed, the camera is not | Tape outline on the tabletop, plus a reference-frame check in the heartbeat. Free |
| Blower fan too loud beside the bed | Blower fans whine | Passive aluminium case, ~€20. At 5fps the fins alone are very likely enough |
| Image too dark | Bounce loss, or an underpowered illuminator | Lengthen exposure first, then reduce the bounce angle, then buy a second illuminator, €12 |
| Image blown out, keypoints poor | Illuminator too close or too narrow | Diffuse it with paper, free, or increase the bounce |

### The one soldering trip

Borrowing an iron means soldering cannot be reactive, so it has to be batched. The sequencing already allows this.

**Nothing is blocked until after the code capture.** The capture needs no iron: the ChunHee button is held directly against the module, so the few centimetres a bare board reaches is plenty, and a wire twisted through the antenna hole is fine for a bench test.

That evening tells you the two things that decide what needs soldering: which frequency the unit uses, and whether the code is fixed or rolling. Buy the consumables then, make one trip, and do both jobs in the same session — the real antenna on the winning transmitter, and, if it proved necessary, the optocoupler on a spare.

---

## The plan

Steps 1 to 3 are done. Steps 4 and 5 were re-sequenced on 22 August 2026 around a constraint the original plan did not have: a first child due 29 August, and therefore no reliable evenings and no second chances at a visit.

| Step | Where | What it answers | Time | State |
|---|---|---|---|---|
| 1. Environment | Laptop | Does pose estimation run at all | 1 hour | Done |
| 2. Calibration session | Laptop, with her | Does sitting up look different | 1 hour | Done, 21 Aug 2026 |
| 3. Detector + replay | Laptop | Does the rule fire correctly | An evening | Done |
| 4. Bench build | **Your kitchen table** | Does the whole rig work at all | Fragments, over weeks | Blocked on the order |
| 5. Install visit | Her room | Is it aimed, online, and visible to you | **One visit, 60–90 min** | After step 4, whenever |
| 6. The week of nights | Her room, **unattended** | How often does it fire on nothing | A week of no attendance | After step 5 |
| 7. Enable the trigger | Over SSH, from anywhere | Does it ring the pager for real | Minutes | After step 6 reads clean |

---

## Re-sequenced for no evenings

The original plan put nearly everything in her bedroom at night. Most of it does not need to be there. Sorting the work by two questions, *does this need her room* and *does this need me awake*, collapses it to a single visit.

**The week of nights costs you no time.** The Pi runs unattended. What that week actually needs is one install and the ability to see what happened from your own flat. It was never a week of your evenings; it was written as though it were.

**The RF capture does not need her room either, and this is the bigger find.** It was sequenced last, in her flat, after the week of nights. There is no reason for it. Two ChunHee buttons and two receivers already exist in that flat — bring one of each home. Pressing a button against the receiver module on a breadboard at your kitchen table answers both of step 5's real questions, which frequency and whether the code is fixed or rolling, in five minutes, months before the Pi moves anywhere.

**So the work sorts into two piles.**

*At home, in fragments, which is the shape of the time a newborn leaves you.* Flash the card and build the stack. Port the capture to picamera2, the hour step 4 budgets. Export NCNN. Write `log_night.py` and the systemd unit. Capture the ChunHee code. Solder both antennas on the single borrowed-iron trip, once the capture has said which frequency won. Bench the replay: transmitter in one room of your flat, her spare receiver in another, and prove the `rpi-lgpio` shim works. Then run the assembled rig overnight at your own place, pointed at your own bed.

None of that is longer than twenty minutes at a stretch. All of it was previously scheduled to happen in her bedroom, at night, in one sitting.

*In her room, once.* Place it, aim it, set `BED_BOX`, take the reference still, tape the base outline, join her WiFi, confirm a frame reaches you from outside the flat, position the illuminator, plug in, leave.

**Install the transmitter during that same visit, with the trigger disabled in software.** This is how the sequencing rule survives without costing a second trip. The rule exists so the pager cannot ring before the false alarm rate is known, and that is about *activation*, not about hardware being present in the room. Screwing the radio box down is physical work and it batches. Turning it on is one line over SSH, weeks later, from your sofa. That is step 7.

**The dependency all of this creates: the heartbeat has to push, not wait to be pulled.** A morning line "somewhere you will actually see" was a nicety in the original plan. It is now load-bearing. If you cannot read the log and cannot reach the Pi from outside her flat, one bad week silently becomes a second visit and then a third, and visits are the thing you no longer have. Both halves are free and neither is a purchase:

- **Tailscale on the Pi.** One install, one login, and you have SSH from anywhere without touching her router or asking anyone for a port forward.
- **A pushed morning summary,** to [ntfy.sh](https://ntfy.sh) or a Telegram bot. No server, no inbox to remember to check.

Build and test both during the rehearsal at your flat. Not in her bedroom, at night, with a sleeping person in it.

**Should the camera build pause? No, but be honest about the date.** Order the hardware: Pi prices are climbing in the DRAM shortage rather than falling, and Mainz to Milan is several days, which lands it around 26 to 28 August. The home pile cannot realistically be finished before the 29th, so the install visit is a post-birth task. Plan it as one. Do not try to squeeze it in beforehand: a rushed install that yields a week of unusable nights, with no remote way to re-aim, costs more than three months of waiting does. Nothing here spoils on the shelf.

---

## Step 1 — Environment

**Python 3.11, on purpose, on both machines.** Raspberry Pi OS Bookworm ships 3.11, so matching it on the laptop means the code from steps 1 to 3 lands on the Pi in the bench build without version differences stacking on top of the camera rewrite you already have to do there. Do not upgrade to a newer Python for this. It buys nothing and introduces a gap between the two machines.

macOS has two Pythons side by side. The one you get by typing `python3` is Apple's 3.9, which is below the floor, and installing packages into it is bad practice regardless. 3.11 is installed separately and is the one you want. So the venv line names it explicitly:

```bash
python3.11 -m venv ~/Documents/code/bed-exit/venv   # note: python3.11, not python3
source ~/Documents/code/bed-exit/venv/bin/activate
pip install ultralytics opencv-python pandas
```

After activation the version is remembered, and plain `python` inside the venv is the right one. Check it once with `python --version` before installing anything.

`ultralytics` pulls in PyTorch, so expect a large download.

The project lives at `~/Documents/code/bed-exit/`: `venv/` for the environment, `scripts/` for the code, `docs/` for a copy of this document. The original of this document stays in the vault and is the one to edit.

Keep the logged CSVs with the scripts that produced them. They are the evidence every threshold is derived from, and a threshold without its session data is just a number someone once believed.

**Model choice: `yolo11n-pose.pt`, for the whole project.** It downloads automatically on first use. Faster models exist, but you are running at 5fps against a 6–12fps budget, so there is no speed problem to solve, and thresholds do not transfer between models. Changing model later means redoing step 2. Pin it and forget it.

Sanity check that it runs:

```python
from ultralytics import YOLO
import cv2

model = YOLO("yolo11n-pose.pt")
cap = cv2.VideoCapture(0)

while True:
    ok, frame = cap.read()
    if not ok:
        break
    r = model(frame, verbose=False)[0]
    cv2.imshow("pose", r.plot())
    if cv2.waitKey(1) == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
```

Stand in front of the webcam. You should see a skeleton drawn on you. If this works, the hard dependency problem is already solved.

**macOS will ask for camera permission the first time this runs**, and the prompt attaches to the terminal app rather than to Python. Grant it. If it runs somewhere that cannot show a prompt, it fails silently with black frames instead of raising an error, which is a confusing hour spent debugging the wrong thing.

**Keypoint indices you'll need** (COCO ordering):

```
0 nose
5 left shoulder     6 right shoulder
11 left hip         12 right hip
13 left knee        14 right knee
15 left ankle       16 right ankle
```

---

## Step 2 — Calibration session

The important one. Everything else is plumbing.

**What this step cannot tell you.** A laptop webcam is not NoIR and has no IR illumination, so this session needs the room lit. That is fine for the question being asked, because whether the torso angle separates lying from sitting is geometry and geometry does not care about wavelength. But it says nothing about whether the skeleton survives a dark room on an IR sensor, which stays open until the Pi is on her bedside table and the week of nights has run. A clean result here is encouraging, not conclusive.

Set the laptop up beside her bed, roughly where the Pi camera will eventually go. Ask her to lie in her normal position, then sit up as she would, a few times. Log the whole thing with a label you set by keypress.

Two things this script does that matter later. It picks the largest person in frame rather than whichever skeleton the model happened to rank first, so a carer at the door or a reflection does not get scored. And it logs confidence for the six keypoints you actually use, split into core and ankles, because a duvet hides ankles while the face keeps an all-17 average looking respectable.

```python
from ultralytics import YOLO
import cv2, csv, math, time

model = YOLO("yolo11n-pose.pt")
cap = cv2.VideoCapture(0)
state = "lying"

CORE   = [5, 6, 11, 12]      # shoulders, hips
ANKLES = [15, 16]

f = open("session.csv", "w", newline="")
w = csv.writer(f)
w.writerow(["t", "label", "torso_angle",
            "sh_x", "sh_y", "hip_x", "hip_y",
            "ankle_l_x", "ankle_l_y", "ankle_r_x", "ankle_r_y",
            "core_conf", "ankle_conf"])

def midpoint(k, a, b):
    return ((k[a][0] + k[b][0]) / 2, (k[a][1] + k[b][1]) / 2)

def pick_person(r):
    """Largest bounding box. Her, in bed, close to camera, beats a carer at the door."""
    if r.keypoints is None or len(r.keypoints.xy) == 0:
        return None
    if r.boxes is None or len(r.boxes) == 0:
        return 0
    areas = [(b[2] - b[0]) * (b[3] - b[1]) for b in r.boxes.xyxy.tolist()]
    return max(range(len(areas)), key=lambda i: areas[i])

while True:
    ok, frame = cap.read()
    if not ok:
        break

    r = model(frame, verbose=False)[0]
    i = pick_person(r)

    if i is not None:
        k = r.keypoints.xy[i].tolist()
        c = r.keypoints.conf[i].tolist()

        sh = midpoint(k, 5, 6)
        hip = midpoint(k, 11, 12)

        # 90 = fully upright, 0 = flat. Image y increases downward.
        dy = hip[1] - sh[1]
        dx = abs(sh[0] - hip[0])
        torso_angle = math.degrees(math.atan2(dy, dx if dx > 1 else 1))

        core_conf  = sum(c[j] for j in CORE) / len(CORE)
        ankle_conf = sum(c[j] for j in ANKLES) / len(ANKLES)

        w.writerow([time.time(), state, round(torso_angle, 1),
                    *[round(v, 1) for v in sh], *[round(v, 1) for v in hip],
                    *[round(v, 1) for v in k[15]], *[round(v, 1) for v in k[16]],
                    round(core_conf, 2), round(ankle_conf, 2)])

        cv2.putText(frame, f"{state}  angle {torso_angle:.0f}  core {core_conf:.2f}  ank {ankle_conf:.2f}",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

    cv2.imshow("calibration", frame)
    key = cv2.waitKey(1)
    if key == ord("l"): state = "lying"
    if key == ord("s"): state = "sitting"
    if key == ord("u"): state = "standing"
    if key == ord("q"): break

f.close()
cap.release()
cv2.destroyAllWindows()
```

### Running the session

**The keys are a switch, not a shutter.** Every frame is written to the CSV automatically, roughly 30 to 60 rows a second, from the moment the script starts. You never capture anything by hand. Pressing `s` tags every frame from that moment onward as `sitting`, and it stays that way until you press something else. You are not photographing poses, you are telling the recording what she was doing at each moment, so the analysis can compare the numbers across states afterwards.

1. Start the script. It begins on `lying`.
2. She is settled and lying normally. Press `l`. Let it record thirty seconds or so of ordinary lying, including her shifting around, because that is the false-alarm baseline.
3. The moment she starts to sit up, press `s`.
4. If she gets to her feet, press `u`.
5. When she settles back down, press `l` again.
6. Repeat the cycle four or five times.
7. Press `q` to stop.

Five to ten minutes in total.

**The keypresses go to the video window, not the terminal.** The window titled "calibration" must be focused or nothing registers. Click it once before you start. You will know it worked because the label text in the top left changes.

**Press when the movement starts, not when it finishes.** A second out does no harm, since the analysis matches fires to labels within a ten second window. Ten seconds out does.

**Rehearse on yourself first.** Five minutes on a sofa. The point is to have the rhythm of clicking the window and hitting the right key already in your hands before you are doing it in front of her, and to find out where the laptop needs to sit.

Keep pressing `l` even if lying detection turns out to be unreliable and you stop caring about it. The labels are not for the detector, they are for `analyse.py`. Without a transition into sitting there is nothing to match fires against, and missed events cannot be counted at all.

**Watch the screen while it runs.** This is the real test:

- Does the skeleton track her at all when she's lying down? Pose models are trained overwhelmingly on upright people. Lying down is out of distribution for them.
- Does it survive the duvet? Watch `ankle_conf` specifically. If it sits low while `core_conf` stays high, the ankle test is worthless and the torso angle is carrying the whole detector.
- Does the torso angle number move clearly between lying and sitting? That's the whole question.

If keypoints are unreliable under the covers, stop and reconsider before buying anything. The mitigations are camera angle, IR contrast, or falling back to whole-body bounding box height rather than skeleton keypoints. Better to hit that wall now.

### Reading the thresholds off

```python
import pandas as pd
d = pd.read_csv("session.csv")
print(d.groupby("label")["torso_angle"].describe())
print(d.groupby("label")[["core_conf", "ankle_conf"]].mean())
```

You want the max angle while lying to sit clearly below the min angle while sitting. If they overlap, the feature is weak and you need a second one.

### What the session actually produced, 21 August 2026

Six recordings, 15:54 to 16:04, about seven and a half minutes of her, in daylight on the laptop webcam at 1920x1080. She was tired after a hospital trip for an MRI that morning, and this is likely the only calibration data there will be for some time. Files live with the scripts.

**The feature works.** Pooled across the usable sessions, torso angle while lying has a median of 26 degrees and a 95th percentile of 61. While sitting or standing the median is 87 and the 5th percentile is 45. Replaying the detector over the labelled data at a 60 degree threshold: **five exits out of five detected, mean latency 2.5 seconds, zero spurious fires across three minutes of labelled lying.** The 2.5 seconds is the sustain window, so detection is effectively immediate once the pose changes. Any threshold from 50 to 80 catches all five; 60 to 65 is the band with no spurious fires, and 60 is the more sensitive end of it.

`TORSO_UPRIGHT_DEG` is therefore set to 60.

**The ankle test is dead, and this is the real finding.** Her ankles sat *further* along the x axis while lying, median 1277px, than while sitting, 1122px, or standing, 1063px. The bed edge idea assumed her feet cross a line outward as she gets up. From where the camera actually stood, the opposite happens. There is no value of `BED_EDGE_X` that separates the two, and any value fires continuously while she sleeps. `ANKLE_TEST` is set to `False` in `detector.py`. It should only be reconsidered against fresh data from the Pi's real mounted position and angle, not restored on the assumption that it was mis-tuned.

So the detector is now a single feature. That is a genuine reduction in robustness and it is worth naming. The decision, taken 22 August 2026, is to leave it single and let the week of nights rule on it rather than building hip height now against data that does not exist. What was added instead is logging, not a feature: `sh_conf`, `hip_conf` and `core_min` go into the night CSV so that a bad night can be diagnosed offline. See *Known risks*.

**Two sessions needed judgement.**

`155421`, the first, is unusable. Its labels run backwards against every other session, lying at a median 55 degrees and sitting at 22, with core confidence at 0.35 in the opening seconds. Something other than her settled pose was in frame, or the keys went in wrong. Excluded rather than repaired, because guessing which is which would put invented ground truth into the one dataset everything else is measured against.

`155517` is the one flagged at the time: the `sitting` label stayed on after she lay back down. The tail from roughly 85 seconds is mislabelled. It was truncated at 80 seconds and only the clean head used. The tail was discarded rather than relabelled, deliberately, since re-cutting labels by reading the torso angle would be using the feature to prove itself.

Truncating it is still a decision that flatters the result, so it is recorded here rather than buried. The three untouched sessions, `155900`, `160015` and `160226`, carry the conclusion on their own.

**What this session did not answer.** She was lightly covered: ankle confidence while lying averaged 0.73, and four frames in five had usable ankles. Under a winter duvet that number collapses, and the whole duvet-occlusion question the research warned about is still completely open. Add to that daylight, an RGB webcam, no IR, and a camera position that is not the one the Pi will occupy. A clean result here was always going to be encouraging rather than conclusive, and that is exactly what it is.

**One caveat on `analyse.py`'s own verdict.** Its separation check compares the absolute min and max, so a single stray frame prints `OVERLAP` even on a session the detector handles perfectly. Read the percentile spread and the fire counts underneath it, not that line.



---

## Step 3 — Detector and replay harness

Write the detection as one function with the thresholds as named constants at the top. Tuning then means changing numbers, never restructuring code.

```python
# ---- tuning constants: this is the only block you edit ----
TORSO_UPRIGHT_DEG   = 45      # above this, torso counts as rising
ANKLE_OUT_MARGIN    = 20      # px beyond bed edge before ankles count as out
SUSTAIN_SECONDS     = 2.5     # how long the condition must hold
MIN_CORE_CONF       = 0.4     # ignore frames where shoulders/hips are guessed
MIN_ANKLE_CONF      = 0.4     # below this, don't score the ankle test at all
MAX_GAP_SECONDS     = 1.0     # a longer blind gap resets the sustain window
BED_EDGE_X          = 900     # x pixel of bed edge, from your frame
# -----------------------------------------------------------

def frame_score(row):
    """Return 0..2, or None if the frame is unusable. Higher means more likely getting up."""
    if row["core_conf"] < MIN_CORE_CONF:
        return None                      # unusable frame, not a negative

    score = 0
    if row["torso_angle"] > TORSO_UPRIGHT_DEG:
        score += 1
    if row["ankle_conf"] >= MIN_ANKLE_CONF and (
            row["ankle_l_x"] > BED_EDGE_X + ANKLE_OUT_MARGIN or
            row["ankle_r_x"] > BED_EDGE_X + ANKLE_OUT_MARGIN):
        score += 1
    return score
```

**These are the original values, kept as the shape of the thing. They are not what runs.** The live constants are in `scripts/detector.py`, set from real data on 21 August 2026: the threshold is 60, not 45, and the ankle half of the score is switched off entirely. See *What the session actually produced* above for why. Read this block for the design, that file for the numbers.

Score rather than AND. Requiring every condition simultaneously makes the alarm quieter and less safe, and a miss costs far more here than a false ring.

**Tune toward firing too often.** This is a decision, not a default: an alarm that goes off when nothing happened is the acceptable failure, and a missed exit is not. So fire on score >= 1, and if the two thresholds land ambiguously, take the lower one. `SUSTAIN_SECONDS` is the exception worth keeping honest, because it is not a sensitivity dial, it is what stops a single misread frame ringing the house at 3am.

One caveat on "any rate is fine," and then it is your call. The number that matters is not how much noise anyone will tolerate, it is the point at which the people being woken stop getting up. If it rings hourly, they will start assuming it is nothing, and a system that is ignored is worse than one that is off, because everyone still believes it is working. So there is no target to hit, but if a night's replay shows fires every hour, that is not a sensitive detector, it is a broken one, and the fix is the thresholds rather than the tolerance.

Note the ankle test is gated on ankle confidence. Under a duvet the model will happily invent ankle positions, and an invented ankle beyond the bed edge is a false alarm generated from nothing.

Then the sustain logic, which is what stops single bad frames triggering:

```python
def run_detector(df, fire_at=1):
    """Replay over a logged CSV. Returns list of fire timestamps."""
    fires, run_start, armed, last_good_t = [], None, True, None

    for _, row in df.iterrows():
        s = frame_score(row)

        if s is None:
            # Unusable frame. If we've been blind too long, the sustain window is void.
            if (run_start is not None and last_good_t is not None
                    and row["t"] - last_good_t > MAX_GAP_SECONDS):
                run_start, armed = None, True
            continue

        # Resuming after a long gap is not a continuation.
        if last_good_t is not None and row["t"] - last_good_t > MAX_GAP_SECONDS:
            run_start, armed = None, True
        last_good_t = row["t"]

        if s >= fire_at:
            if run_start is None:
                run_start = row["t"]
            elif armed and row["t"] - run_start >= SUSTAIN_SECONDS:
                fires.append(row["t"])
                armed = False            # don't re-fire continuously
        else:
            run_start, armed = None, True

    return fires
```

`MAX_GAP_SECONDS` matters more than it looks. Without it, one high-scoring frame, then forty seconds of occlusion, then one more high-scoring frame satisfies the sustain window and fires. The window silently spans the blind gap. Since occlusion is the exact failure mode this project lives or dies on, that bug would have fired the alarm precisely when the camera could see least.

**How you modify detection.** Change a constant, rerun `run_detector` over every CSV you've logged, count two numbers separately:

```python
fires = run_detector(d)
# true positives: fires within ~10s of a label change to sitting/standing
# false positives: everything else
```

Missed events and false alarms per night are different currencies. Never collapse them into one accuracy figure. One false alarm a night is survivable. One an hour gets the box unplugged.

If a single feature won't separate cleanly, add a third: vertical position of the hip midpoint. Rising off a mattress moves the hips upward before the torso finishes rotating.

---

## Step 4 — Bench build, at your kitchen table

The hardware is ordered. **Everything in this step happens at your flat.** Nothing below needs her room, and the parts that do are in step 5.

### Do this the hour the box arrives

Open the box, take out the microSD card, and flash it. Nothing else. Not the case, not the camera ribbon, not the illuminator.

It is first because it is the only task in the entire build that needs no assembly, no soldering, no bench time and no uninterrupted evening. It is twenty minutes at a laptop, it can be done one-handed with a newborn on your shoulder, and until it is done every other step is blocked. It is also where the two decisions live that are painful to undo later: the OS version, and whether the Pi can be reached without a monitor.

**Reading the card: settled.** The MacBook has a full-size SD slot, and the card ships with a full-size adapter, so card into adapter into slot. No reader to buy. Checked 23 August 2026, so nobody needs to raise it again.

1. Install [Raspberry Pi Imager](https://www.raspberrypi.com/software/) on the Mac.
2. Choose the OS explicitly: **Raspberry Pi OS Bookworm, 64-bit**, full rather than Lite. Bookworm is no longer the default offer, so go into Imager's "Other" OS list and pick it. Taking whatever sits on top gets you Trixie and a newer Python than picamera2 and ultralytics are settled on together, and you will spend an evening on version drift instead of the project.
3. **Open the advanced options before writing**, and set: hostname `bedcam`, your username and password, WiFi name and password for *your* flat, locale, and **enable SSH**. This is the step that means the Pi never needs a monitor, a keyboard or an HDMI cable, none of which you own for it. Getting it wrong means finding a screen or reflashing.
4. Write, wait, eject.
5. Label the card or the adapter. A blank microSD looks exactly like every other blank microSD.

Her WiFi goes in later, during the install visit. Right now it wants yours, because the whole of step 4 happens at your kitchen table.

**On the 8GB board, full is fine.** The desktop costs several hundred megabytes to run something you will rarely look at, since the imager has already set up headless SSH and every instruction from here down is a command line. The board absorbs that without the detector ever noticing.

### Then, when you have an evening

**On the 8GB board, full is fine.** The desktop costs several hundred megabytes to run something you will rarely look at, since the imager has already set up headless SSH and every instruction from here down is a command line. The board absorbs that without the detector ever noticing.

**First boot.**

```bash
ssh you@bedcam.local
sudo apt update && sudo apt full-upgrade -y
sudo apt install -y python3-opencv
rpicam-hello --list-cameras          # confirm the camera is seen
rpicam-vid -t 5000 -o test.h264      # confirm capture works
```

**Install.** Use a venv with system packages visible, because `picamera2` and OpenCV are installed at system level:

```bash
python -m venv --system-site-packages ~/bedexit
source ~/bedexit/bin/activate
pip install ultralytics pandas
```

Expect this to be slow on ARM. If pip resolution errors out, install `torch` from the piwheels index first. Do not `pip install opencv-python` here; the apt package is already visible to the venv and building the wheel on ARM is a long, avoidable detour.

**The capture code is different on the Pi.** This is the one part of step 2 that does not port. The Camera Module 3 is a CSI camera, and on Bookworm those go through libcamera and picamera2, not the V4L2 path `cv2.VideoCapture(0)` expects. Budget an hour.

```python
from picamera2 import Picamera2

picam2 = Picamera2()
picam2.configure(picam2.create_video_configuration(
    main={"size": (1280, 720), "format": "RGB888"}))
picam2.start()

frame = picam2.capture_array()       # feed this to model(frame) as before
```

Everything downstream of `frame` is unchanged from step 2. Keep `pick_person`, keep the split confidence logging, drop the keyboard labels.

**Speed it up.** Export the model to NCNN, which is meaningfully faster on ARM:

```python
from ultralytics import YOLO
YOLO("yolo11n-pose.pt").export(format="ncnn")
```

Then load `yolo11n-pose_ncnn_model` instead of the `.pt`.

**Which person is her.** `pick_person` no longer takes the largest bounding box. That rule assumed any other person in frame would be far away, at the door. In this room the opposite is true: whoever is caring for her stands *between* the camera and the bed, so they are the nearest thing in shot and the largest box in it. A standing adult also reads about 90 degrees of torso angle at high confidence, which is a fire, sustained for exactly as long as they stand there. That is not an edge case, it is every time somebody straightens the bedding.

**A positional rule alone does not fix this, which was found out the hard way on 22 August.** Perspective puts a standing person's hips, and their bounding box centre, *inside* the bed rectangle: measured, a passer-by's hips landed at (339, 208) against a bed box of (42, 142, 788, 510). Box size does not separate them either, because the camera is on the bedside table, so she is as close to it as they are: 454 pixels tall sitting up, against their 517.

What separates them is the head. A camera at mattress height cannot see the head of anyone standing beside it. The model still fits them a skeleton and still reports about 90 degrees of torso angle, but it is extrapolating a head it cannot see, and its confidence says so: 0.01 and 0.02 for the two passers-by that caused false alarms, against 0.99 for her both lying and sitting up.

So the rule is two layers, in this order. Reject anyone whose nose confidence is below `MIN_NOSE_CONF`, which removes everyone close to the lens, exactly where position fails. Then, of those left, take the one whose box centre falls inside `BED_BOX`, which catches the far case the first layer allows through: someone upright at the door, head in frame, small in the picture. Return nobody if the bed is empty.

Replayed over the 22 August recording, frame for frame: the old largest-box rule fired five times, four of them false. The two-layer rule fired once, on the real exit, at the identical timestamp.

Full reasoning, and the scenarios that shaped it, are in `scenarios-and-decisions.md`. Read it before changing this.

`BED_BOX` cannot be set from the calibration CSVs, which log keypoints and not boxes. It comes off a still at the real mount, so it is set during the install visit.

**Night run.** Run at 5 fps, log keypoints to CSV, and save short video clips only when the detector would have fired, so you can check whether the numbers told the truth.

Carry `pick_person` and the confidence columns over from `calibrate.py` unchanged. The logger writes `sh_conf`, `hip_conf` and `core_min` alongside `core_conf`. Nothing reads them yet and the firing rule is unchanged; they exist so that if a night ever looks wrong, you can tell a duvet-hidden hip from a bad threshold by replaying the CSVs, instead of needing another session with her. There will not be another session with her for months, which is the whole reason to spend one line on it now.

**Run it as a service, not a cron line.** A 22:00 cron entry starts the job and nothing restarts it when it dies at 01:30. Dying quietly at 01:30 is the exact failure this document opens by warning about, and a cron line cannot tell you it happened.

```ini
# /etc/systemd/system/bedcam.service
[Unit]
Description=Bed exit logger
After=network.target

[Service]
User=you
ExecStart=/home/you/bedexit/bin/python /home/you/log_night.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable --now bedcam
```

**And add a heartbeat.** Every morning, one line somewhere you will actually see: ran 22:00 to 08:00, N frames, N fires, N restarts. Without it you cannot tell a quiet night from a dead process, and you will spend a week trusting a log that stopped on Tuesday.

Add one number to that line: the mean absolute difference between the night's first frame and a saved reference still. A jump means the camera was moved, which is otherwise completely silent and quietly invalidates every threshold you own. Twenty lines of code against the failure mode this document opens by warning about.

**Two things that will bite.**

Undervoltage corrupts SD cards silently. Use the official 27W supply and nothing else, and check `vcgencmd get_throttled` returns `0x0`. Note this line used to add "and the illuminator draws from the Pi's USB budget too"; that stopped being true with the 21 August revision, and the illuminator now shares no rail with the Pi at all.

Disk filling is the classic failure. Delete oldest files when free space drops below a threshold rather than letting the card fill.

**Rehearse the whole thing at your flat before it goes anywhere.** Assemble the finished rig, point it at your own bed or the sofa, and run it overnight. You are not testing detection here, you are testing everything around it: that the service comes back after `kill -9`, that it survives a reboot, that the disk pruning fires, that WiFi reconnects after the router drops, and that the morning summary actually reaches your phone.

This is the single highest-value hour in the project now. Nearly everything that would otherwise burn a visit to her flat fails here first, where failing costs nothing.

### Keeping other people out of it

This is a camera in a bedroom belonging to someone who cannot check on it herself, so the standard is higher than for a doorbell. The good news is that the design is already most of the way there, mostly by accident: **there is nothing to connect to.** No cloud account, no vendor service, no web interface, no RTSP stream. The Pi never sends video anywhere. Clips are files on a card in her bedroom, and the CSVs are columns of numbers.

The threats worth spending effort on, in order of how likely they are to actually happen.

**Never forward a port on her router. Not once, not temporarily.** This is the single decision that matters. Nearly every "hacked baby monitor" story is either a vendor cloud breach or a device exposed directly to the internet on a forwarded port. Tailscale is what makes forwarding unnecessary: it builds an encrypted private network between your own devices, nothing listens on the public internet, and the Pi is unreachable from anywhere you have not explicitly joined. If you ever find yourself following a guide that says "forward port 22", stop.

**Your Tailscale login is now the key to the house.** Put two-factor authentication on it, and on whichever account you sign into it with. That account is a more attractive target than the Pi.

**Turn off SSH password login** once your key works, since her WiFi password is likely on a fridge magnet:

```bash
ssh-copy-id marco@bedcam.local          # from the Mac, before you disable anything
sudo sed -i 's/^#*PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo systemctl restart ssh
```

Do it in that order, and keep the current session open until you have proved a new one works.

**Let it patch itself**, since nobody is going to remember to:

```bash
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

**Keep less.** Clips are written only when the detector fires, pruned when the card fills, and there is no reason to keep them once a night has been reviewed. The CSVs are the evidence worth keeping and they contain no images.

**The heartbeat topic is a password.** An ntfy topic name is all anyone needs to read it, so it carries a random suffix. It reveals no video, but it does reveal when she is alone and when she gets up, which is not nothing.

**Physical access is total access.** Anyone who can pick up the Pi can read the card. Full-disk encryption on a headless machine that must boot unattended is more trouble than it is worth here, so this is accepted rather than solved: the mitigation is that the rig sits in her bedroom in her flat.

**What is deliberately not being done.** No VPN on the router, no fail2ban, no firewall rules. With no open ports and key-only SSH there is no exposed surface for them to protect, and each one is another thing that can break at 3am in a flat you are not in.

**Remote observability, built here and not there.** Install Tailscale on the Pi and confirm you can SSH in over mobile data with your own WiFi off. Point the morning heartbeat at ntfy.sh or a Telegram bot and confirm it lands. Both are free. Neither can be debugged in her bedroom at midnight.

---

## Step 5 — Install visit

One visit, and everything physical happens in it. Sixty to ninety minutes if step 4 was rehearsed properly, an entire evening if it was not.

Run it as a checklist, because you will be doing it tired.

1. Rig on the fixed bedside table, camera at 0.80m to 1.00m, shooting across the bed from the side she does *not* get out of. Not the foot of the bed, where legs occlude each other.
2. Take a still. Look at it. Move it. Repeat until she is fully in frame lying down, with headroom for sitting up.
3. **Set `BED_BOX`** off that still, generous enough to hold her both lying and sitting. Restart, and check the overlay draws the rectangle where you meant it.
4. Watch the live readout for a minute with her in bed. `hip` should not be sitting near zero. If it is, drop the camera a little or change the angle before you leave, because this is the one thing you cannot fix over SSH.
5. Tape an outline of the camera base on the tabletop. The table is fixed but the ball head is not, and a knock during cleaning shifts the frame without anyone noticing.
6. Illuminator on its own wall socket, bounced off the wall behind the camera at roughly 45°. Nothing runs between it and the Pi.
7. Join her WiFi. Confirm from your phone, on mobile data, that you can reach the Pi over Tailscale and pull a frame.
8. **Mount the radio box and wire the transmitter, but leave the trigger disabled.** The hardware batches into this visit; switching it on is step 7 and happens from your sofa.
9. Save the reference still the heartbeat compares against.
10. Start the service. Leave.

Then step 6 runs itself. A week of nights, nobody in attendance, and you read the CSVs from home. Replay the detector over them and count.

---

## Step 6 — The RF work

Split by where it happens. Everything except the last line is at your kitchen table, and most of it can be done before the install visit rather than after it.

**Capture the code first, before wiring anything permanent.** Everything below assumes fixed learning codes, which is what the ChunHee range uses. Verify it in five minutes: run the receive script, press a spare ChunHee button next to the module, and read what it prints. Press it several times. Same number every time means you are fine. A number that changes each press means rolling code, and the replay route is dead; skip to the fallback at the bottom of this section.

If the 433.92MHz receiver prints nothing at all, do not assume anything is broken. Silence is what the wrong frequency looks like, but it is also what an underpowered receiver looks like, so try the 5V-plus-divider wiring below before concluding anything about frequency. If it is still silent after that, swap in the 315MHz pair. It is in the box for exactly this, so that a wrong guess about frequency cannot cost you the evening.

**Wiring.** Transmitter data to GPIO 17, receiver data to GPIO 27, both grounded to the Pi.

The transmitter can take 5V power and accepts 3.3V logic on its data pin, so it wires directly. Higher supply voltage just improves its range.

**The receiver cannot.** Powered at 5V it puts 5V on its data line, and the Pi's GPIO is 3.3V with no tolerance for more. Straight into GPIO 27 that damages the pin, and it tends to show up as intermittent flakiness rather than an honest failure. This is the only place in the build that can actually damage the Pi, so it gets a rule rather than a choice.

> **The receiver never touches the 5V rail.** VCC to pin 1 (3.3V), GND to pin 6, data to GPIO 27 (pin 13) **through a 10k resistor in series**.

Two independent protections, and neither of them asks you to be careful at 11pm.

The 3.3V supply is the one that matters, because it is an elimination rather than a mitigation. A chip cannot output more than its own supply rail, so with VCC on pin 1 the data pin physically cannot present more than 3.3V whatever else goes wrong. A divider, by contrast, only works if you wired the divider correctly.

The 10k in series is the backstop. Even if 5V somehow reached that line, 10k limits current into the pin's clamp diodes to under 200µA, which is orders of magnitude below anything that harms silicon. It is the same resistor the divider would have used, and it costs nothing out of the assortment.

**The sensitivity objection does not apply here.** The XY-MK-5V is designed for 5V and loses range at 3.3V. Irrelevant: you are holding the ChunHee button against the module.

**If it is genuinely dead at 3.3V,** then and only then go to 5V with the full divider: 10k in series, 20k from the GPIO side to ground. Do it deliberately, on the bench, with the Pi powered off, as a considered fallback rather than the default.

**Yes, all of this happens on the breadboard.** That is what the mini breadboard in the radio box is for, and the mechanics matter more than the theory.

Both modules have 2.54mm pin headers, so they push straight into the board. The Dupont jumpers then run from the breadboard rows to the Pi's GPIO header. The resistor is the part people get wrong: it has to bridge **two different rows**, with the receiver's data pin in one and the jumper to GPIO 27 in the other. Both legs in the same row does nothing at all, because a breadboard row is already a short. If in doubt, tug-test it: the signal has to be forced through the resistor, not offered a way around it.

**The 170-contact mini breadboard has no power rails**, and does not need any. It is the central strip only, five rows either side of the gap. Power reaches each module by a female-to-male jumper running straight from the Pi's header into whichever row that module's VCC pin occupies. Rails only earn their place when several components share a supply, and here nothing does.

Earlier versions of this section said to put the transmitter's 5V and the receiver's 3.3V on opposite power rails. That instruction assumed a larger board and is void. The rule below replaces it and is better anyway, because it removes the hazard rather than separating it.

**Better still, do not have them coexist.** The receiver is a bench instrument, not part of the finished rig: it exists to read the ChunHee code once, and after that it has no function. Capture the code with the receiver alone on the board, write the number down, then pull the receiver out before wiring the transmitter for replay. The deployed box contains one module, one supply voltage, and no 5V-into-GPIO risk at all. Keep the receiver in a drawer for the day something stops working.

**Antennas, both modules.** A bare FS1000A reaches a few centimetres. Solder or twist 17.3cm of solid core wire onto each antenna pad, which is a quarter wave at 433.92MHz. Skip this and you will conclude the replay failed when it simply did not reach the next room.

```bash
pip install rpi-rf
```

**Pi 5 gotcha, check before you debug anything else.** The Pi 5's new I/O chip broke the old `RPi.GPIO` library that `rpi-rf` depends on. The `rpi-lgpio` shim is the usual drop-in fix. Confirm this works before assuming the RF side is at fault, because it is the single most likely place to lose an evening.

**Replay it, at your flat.** Send the captured code and confirm the receiver rings from the next room. Do this at home with her spare receiver, not in her flat. It proves the antenna, the shim and the range all at once, and it is the last thing that has to work before the trigger is worth enabling.

**Step 7 is what remains, and it is not a visit.** Once the week of nights reads clean, connect the detector's fire event to the same function and restart the service over SSH. Minutes, from anywhere.

**Two design rules.** Pair a spare transmitter, never the one she uses to call for help. And give the spare its own melody in the receiver, so whoever wakes at 3am knows instantly whether she pressed the button or the camera fired. The receivers hold up to 50 buttons with per-button ringtones, so this costs nothing but the pairing.

**Fallback if any of this stalls.** Solder an optocoupler across a spare transmitter's switch contacts, driven from a GPIO pin. An hour of fiddly work, but it sidesteps rolling codes, sidesteps `rpi-rf`'s bit-banged timing on the Pi 5, and cannot fail in the "worked on the bench, doesn't reach at 3am" way a bare FS1000A can. RF replay is the more elegant path and worth one evening, given the codes are almost certainly fixed. If it starts consuming a second evening, the optocoupler is the better system, not a consolation prize.

---

## Sequencing rule

Do not order until step 3 shows clean separation on the calibration data. Done, 21 August 2026.

Do not go to her flat until the rig has run a full night at yours. Do not enable the trigger in step 7 until the week of nights in step 6 shows an acceptable false alarm rate. Every step exists to kill the project cheaply if the answer is no.

The rule that makes the single visit legal: **installing the transmitter is not enabling it.** Hardware batches into step 5, activation waits for step 6's numbers, and the gap between them is one line over SSH.

And none of it is coverage. Her husband in the next room is, for as long as this takes.

---

## Known risks

**Occlusion, downgraded 22 August 2026 but not closed.** Pose models are trained overwhelmingly on upright, visible people, and lying under a duvet is out of distribution. What lowers the risk here is behavioural rather than technical: she takes the blanket off first and then sits up, observed directly and visible in the calibration footage. If the blanket is clear before the torso angle starts climbing, the hips are visible at the moment the feature is measured, and the whole problem largely dissolves.

That is an observation about how she actually moves, and it is better evidence than an inference from the code. It is not proof, because it has only been seen in daylight under a light cover, and because the torso angle is a vector from shoulders to hips rather than a shoulders-only reading, so it is the hip end that has to stay visible. The week of nights rules on it. The confidence columns exist so that it rules cleanly.

**Threshold, not detection.** Detecting a body is solved. Separating her normal sleep from a genuine attempt to rise is the real problem. She sleeps propped on cushions, so her baseline is already partly upright.

**No false positive rate from the calibration session.** Step 2 gives you thresholds that fire correctly on a deliberate, awake demonstration. It tells you nothing about how often they fire on nothing. Only the overnight runs answer that.

**Other people in the room, handled but worth watching.** Whoever cares for her stands between the camera and the bed, which made them the nearest and largest figure in frame and would have fired the detector for as long as they stood there. `BED_BOX` replaces the largest-box rule with a positional one and should end it. Confirm on the first night's clips rather than assuming, because it is the failure mode most likely to get the box unplugged, and a system nobody tolerates is worse than one that misses.

**A single feature, knowingly.** The ankle test is dead and nothing replaced it, so `torso_angle` is the whole detector. The decision is to wait for real overnight data rather than build hip height as insurance against a failure nobody has seen. The cost if that is wrong is not a wasted week but a wasted visit, which is why the night log carries `sh_conf`, `hip_conf` and `core_min`: so the fix can be derived from data already in hand instead of from a calibration session that will not be available for months.

**Warning time.** Legs off the bed means she is already moving, which is less warning than a torso-based trigger gives. A two-tier alarm was considered and deliberately rejected in favour of keeping the system simple. One trigger, one outcome.

**Rolling code.** Unlikely, since the ChunHee range uses learning codes, but not confirmed against your specific unit until the capture in step 6. If it turns out to be rolling, RF replay fails and the optocoupler fallback applies.
