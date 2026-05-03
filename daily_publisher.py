import os
import json
import glob
import random
import requests
import shutil
import sys
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
from pathlib import Path
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)

# Import upload functions
try:
    from upload.upload_instagram import upload_to_instagram
    from upload.upload_threads import upload_to_threads
    from upload.upload_facebook import upload_to_facebook, upload_to_facebook_story
    from upload.upload_to_youtube import upload_to_youtube
except ImportError as e:
    print(f"Error importing upload modules: {e}")
    # Still want to proceed or stop?
    pass

PROCESSED_DIR = "Processed_Videos"
PUBLISHED_LOG = "published_videos.json"

def get_already_published():
    if os.path.exists(PUBLISHED_LOG):
        with open(PUBLISHED_LOG, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []


def get_repost_counts():
    """Count how many times each video has been posted."""
    published = get_already_published()
    counts = {}
    for entry in published:
        vname = entry.get("video_name", "")
        counts[vname] = counts.get(vname, 0) + 1
    return counts

def mark_as_published(video_name, metadata):
    published = get_already_published()
    published.append({
        "video_name": video_name,
        "metadata": metadata
    })
    with open(PUBLISHED_LOG, 'w', encoding='utf-8') as f:
        json.dump(published, f, indent=4)

def select_video(specific_video=None):
    published = [item["video_name"] for item in get_already_published()]
    all_videos = sorted(glob.glob(os.path.join(PROCESSED_DIR, "*.mp4")))

    if specific_video:
        # specific_video might be a full path or just a filename
        if os.path.exists(specific_video):
            # It's a full path
            vid_path = specific_video
            name = os.path.basename(specific_video)
        else:
            # It's just a filename, join with PROCESSED_DIR
            vid_path = os.path.join(PROCESSED_DIR, specific_video)
            name = specific_video

        if os.path.exists(vid_path):
            if name in published:
                post_count = sum(1 for p in published if p == name)
                print(f"🔄 Video {name} was already published ({post_count}x) - Re-publishing (recycling)")
            return vid_path, name
        else:
            print(f"❌ Error: Specific video {name} not found")
            return None, None

    # Find unpublished videos first
    unpublished = [(vid, os.path.basename(vid)) for vid in all_videos if os.path.basename(vid) not in published]

    if unpublished:
        vid, name = unpublished[0]
        return vid, name

    # All videos published - use weighted random selection (less posted = more likely)
    if all_videos:
        repost_counts = get_repost_counts()
        weights = []
        for vid in all_videos:
            name = os.path.basename(vid)
            count = repost_counts.get(name, 0)
            weight = max(1, 1000 // (3 ** min(count, 6)))
            weights.append(weight)

        selected_vid = random.choices(all_videos, weights=weights, k=1)[0]
        name = os.path.basename(selected_vid)
        post_count = repost_counts.get(name, 0)
        print(f"🎲 All videos published. Weighted random reuse (posted {post_count}x): {name}")
        return selected_vid, name

    return None, None

def generate_caption():
    import random
    import time

    api_key = os.getenv("POLLINATIONS_API_KEY")
    model = os.getenv("AI_MODEL", "openai")

    fallback_titles = [
        "Tom and Jerry: Classic Cat and Mouse Chaos! 🐭🐱",
        "The Ultimate Rivalry: Tom vs Jerry 🥊",
        "Tom's Latest Scheme Goes Wrong! 😂",
        "Jerry's Clever Escapes: Unstoppable Mouse! 🧀",
        "Classic Moments: Tom and Jerry Fun 📺",
        "Mouse Trap Mayhem: Jerry Wins Again! 🐭",
        "Tom's Hilarious Fails! 😹",
        "Jerry the Genius: Outsmarting Tom 🧠",
        "Legendary Duo: Tom and Jerry's Best Bits ✨",
        "Infinite Chase: The Fun Never Ends! 🏃‍♂️💨",
        "Sneaky Jerry and Grumpy Tom 😼",
        "Whack! Boom! Classic Tom and Jerry Slapstick 💥",
        "Who's Winning Today? Tom or Jerry? 🤔",
        "A Slice of Cheese and a Lot of Trouble 🧀🐁",
        "The Best of Childhood Memories: Tom & Jerry 🏠",
    ]

    fallback_descriptions = [
        "The world's most famous cat and mouse duo are back at it! 🐱🐭 Watch as Tom tries his best to catch Jerry, but we all know who really runs the house. Classic slapstick humor that never gets old! 😂 If you love Tom and Jerry, hit that SUBSCRIBE button for your daily dose of nostalgia! 📺✨ #tomandjerry #classiccartoons #catandmouse #funny #nostalgia #animation #shorts #reels",
        "Tom vs Jerry: The battle for the ultimate cheese slice! 🧀 Jerry's quick wit and Tom's unfortunate luck make for the perfect comedy. Who are you rooting for? Drop a 🐭 for Jerry or a 🐱 for Tom in the comments! 🥊🔥 #tomandjerry #cartoonmemories #funnyvideos #childhood #slapstick #shorts #reels",
        "Another day, another failed trap! 😹 Tom never learns, and Jerry never stops being three steps ahead. Relive the best moments of this legendary rivalry. 🏃‍♂️💨 Join our community of cartoon fans and let's laugh together! 🌟 Like and share with someone who grew up with this! 🐭💥 #tomandjerry #classiccomedy #animation #funnycat #smartmouse #shorts #reels",
        "Jerry the Genius strikes again! 🧠 From mouse traps to clever hiding spots, Tom just can't catch a break. Watch the chase unfold in this classic clip. Smash that LIKE button if you're team Jerry! ⭐ #tomandjerry #cartoonhumor #nostalgia #childhoodmemories #funny #shorts #reels",
        "Childhood wouldn't be the same without Tom and Jerry! 🏠 The traps, the chases, and the ultimate friendship-rivalry. Discipline? No, just pure chaos! ⚡ Follow for daily Tom and Jerry laughs! What's your favorite Tom and Jerry moment? Comment below! 👇 #tomandjerry #classiccartoons #funnyvideos #animation #childhood #shorts #reels",
    ]

    if not api_key:
        chosen_title = random.choice(fallback_titles)
        chosen_desc = random.choice(fallback_descriptions)
        print("Warning: POLLINATIONS_API_KEY not found. Using fallback captions.")
        return chosen_title, chosen_desc

    vibes = [
        "high energy and chaotic — focus on the fast-paced chases and slapstick humor",
        "nostalgic and classic — capture the feel of original Tom and Jerry cartoons",
        "funny and lighthearted — highlight the hilarious fails and clever escapes",
        "clever and witty — focus on Jerry's intelligence and Tom's elaborate traps",
        "dramatic and intense — mock-serious tone about the 'epic' rivalry",
        "playful and mischievous — focus on the pranks and tricks played on each other",
        "action-packed and bouncy — focus on the movement, whacks, and booms",
    ]
    chosen_vibe = random.choice(vibes)

    prompt = (
        f"Write a completely unique, funny, and nostalgic Tom and Jerry themed title and description. "
        f"The content features classic cat and mouse chases, clever traps, and hilarious slapstick comedy. "
        f"Speak as a passionate cartoon fan or a classic narrator — enthusiastic, fun, and nostalgic. "
        f"IMPORTANT: Do NOT use generic openers like 'Welcome back' or 'Welcome to our channel'. Start directly with something engaging. "
        f"Make the vibe {chosen_vibe}. "
        f"The description should be engaging (3-5 sentences), packed with cartoon humor, and full of personality. "
        f"Include engagement calls-to-action such as: "
        f"- Subscribe for your daily Tom and Jerry nostalgia! "
        f"- Comment 'TEAM JERRY' or 'TEAM TOM'! "
        f"- Share this with someone who loves classic cartoons! "
        f"- Smash that LIKE button if you miss the good old days! "
        f"Include relevant hashtags in ALL LOWERCASE such as #tomandjerry #classiccartoons #funny #nostalgia #animation #childhood #catandmouse #shorts #reels. "
        f"Return ONLY a valid JSON object in this format: {{\"title\": \"<title>\", \"description\": \"<description>\"}} "
        f"Do not include any other text or markdown block backticks."
    )


    url = "https://gen.pollinations.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.9,
        "seed": random.randint(1, 999999)
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        content = data.get('choices', [{}])[0].get('message', {}).get('content', '')

        content = content.replace("```json", "").replace("```", "").strip()
        result = json.loads(content)

        chosen_title = random.choice(fallback_titles)
        chosen_desc = random.choice(fallback_descriptions)
        return result.get("title", chosen_title), result.get("description", chosen_desc)
    except Exception as e:
        print(f"Error generating caption: {e}")
        return random.choice(fallback_titles), random.choice(fallback_descriptions)

def main():
    print("=" * 60)
    print("🚀 DAILY AUTOMATION STARTING")
    print("=" * 60)
    
    specific_video = sys.argv[1] if len(sys.argv) > 1 else None
    video_path, video_name = select_video(specific_video)
    if not video_path:
        print("✅ No new videos found to publish. Exiting.")
        return
        
    print(f"👉 Selected Video: {video_name}")
    print("🧠 Generating caption via Pollination AI...")
    title, description = generate_caption()
    
    print(f"📝 Title: {title}")
    print(f"📝 Description:\n{description}")
    
    # Combined caption for platforms that use a single text field
    combined_caption = f"{title}\n\n{description}"
    
    success_flags = {
        "instagram_reel": False,
        "instagram_story": False,
        "facebook_reel": False,
        "facebook_story": False,
        "threads": False,
        "youtube": False
    }
    
    # Instagram Reels
    try:
        result = upload_to_instagram(video_path, combined_caption, is_story=False)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Instagram Reel: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["instagram_reel"] = True
    except Exception as e:
        print(f"❌ Instagram Reel upload failed: {e}")
        
    # Instagram Stories
    try:
        result = upload_to_instagram(video_path, combined_caption, is_story=True)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Instagram Story: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["instagram_story"] = True
    except Exception as e:
        print(f"❌ Instagram Story upload failed: {e}")
        
    # Facebook Reels
    try:
        result = upload_to_facebook(video_path, description, title=title)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Facebook Reel: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["facebook_reel"] = True
    except Exception as e:
        print(f"❌ Facebook Reel upload failed: {e}")
        
    # Facebook Stories
    try:
        result = upload_to_facebook_story(video_path)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Facebook Story: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["facebook_story"] = True
    except Exception as e:
        print(f"❌ Facebook Story upload failed: {e}")
        
    # Threads
    try:
        result = upload_to_threads(video_path, combined_caption)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Threads: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["threads"] = True
    except Exception as e:
        print(f"❌ Threads upload failed: {e}")
        
    # YouTube Shorts
    try:
        upload_to_youtube(video_path, title, description, tags=["tomandjerry", "classiccartoons", "funny", "nostalgia", "animation", "childhood", "catandmouse", "shorts", "reels"])
        success_flags["youtube"] = True
    except Exception as e:
        print(f"❌ YouTube upload failed: {e}")
        
    # Record as published regardless of partial success,
    # to avoid repeating the same video. Alternatively, only record if fully successful.
    print("\n✅ Marking video as published.")
    
    # Check if this is a recycled video (already in published_videos.json)
    published_list = get_already_published()
    is_recycled = any(item["video_name"] == video_name for item in published_list)
    
    if is_recycled:
        print(f"   🔄 This is a recycled video (re-publishing)")
    
    mark_as_published(video_name, {
        "title": title,
        "description": description,
        "success_flags": success_flags,
        "recycled": is_recycled
    })
    
    # Move the published video to Published_Videos folder
    published_dir = "Published_Videos"
    if not os.path.exists(published_dir):
        os.makedirs(published_dir)
        
    try:
        dest_path = os.path.join(published_dir, video_name)
        shutil.move(video_path, dest_path)
        print(f"📦 Moved published video to {dest_path}")
    except Exception as e:
        print(f"❌ Failed to move published video: {e}")
    
    print("🎉 DAILY AUTOMATION COMPLETE")

if __name__ == "__main__":
    main()
