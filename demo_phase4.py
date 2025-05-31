#!/usr/bin/env python3
"""Phase 4 Demo Script

Demonstrates the core business logic components working together:
- Script segmentation
- Prompt enhancement
- Output management
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from aiva_cli.core import (
    segment_script, 
    enhance_prompt, 
    StylePreset,
    create_project,
    SegmentOutput
)


def demo_phase4():
    """Demonstrate Phase 4 functionality."""
    print("🎬 AIVA CLI Phase 4 Demo")
    print("=" * 40)
    
    # Sample 5-minute script about AI
    sample_script = """
    Welcome to the fascinating world of artificial intelligence, where machines learn to think and solve problems like humans.
    Today we'll explore how AI is transforming industries and reshaping our future in ways we never imagined possible.
    
    Machine learning algorithms are the backbone of modern AI systems, processing vast amounts of data to find hidden patterns.
    These intelligent systems can recognize images, understand speech, and even predict future trends with remarkable accuracy.
    From recommendation engines to autonomous vehicles, AI is quietly revolutionizing every aspect of our daily lives.
    
    In healthcare, AI-powered diagnostic tools are helping doctors detect diseases earlier and more accurately than ever before.
    Medical imaging systems can now spot tumors that human eyes might miss, potentially saving countless lives through early intervention.
    Drug discovery, once a decades-long process, is being accelerated by AI algorithms that can predict molecular behavior.
    
    The transportation industry is experiencing a complete transformation through autonomous vehicle technology and smart traffic systems.
    Self-driving cars use computer vision and sensor fusion to navigate complex environments safely and efficiently.
    Meanwhile, AI optimizes traffic flow in smart cities, reducing congestion and emissions while improving urban mobility.
    
    Financial services have embraced AI for fraud detection, risk assessment, and algorithmic trading with impressive results.
    Banks can now identify suspicious transactions in milliseconds, protecting customers from financial crimes and identity theft.
    Investment firms use machine learning to analyze market trends and make split-second trading decisions.
    
    However, with great power comes great responsibility, and we must address the ethical implications of AI development.
    Issues like algorithmic bias, privacy concerns, and job displacement require careful consideration and proactive solutions.
    We need robust frameworks to ensure AI systems are fair, transparent, and beneficial for all members of society.
    
    Looking ahead, the future of AI holds incredible promise for solving humanity's greatest challenges.
    From climate change to space exploration, AI will be our partner in tackling problems that seemed impossible just decades ago.
    The key is ensuring that as we advance these technologies, we maintain human values and ethical principles at their core.
    """
    
    print("\n📝 Step 1: Script Segmentation")
    print("-" * 30)
    
    # Segment the script into 38 parts
    segments = segment_script(sample_script, target_segments=38, target_duration=8.0)
    
    print(f"✅ Created {len(segments)} segments")
    print(f"📊 Total duration: {sum(s.duration for s in segments):.1f} seconds")
    print(f"📊 Average duration: {sum(s.duration for s in segments) / len(segments):.1f} seconds")
    
    # Show first few segments
    print("\n🔍 Sample segments:")
    for i, segment in enumerate(segments[:3]):
        print(f"   Segment {segment.index}: {segment.text[:60]}... ({segment.duration:.1f}s)")
    
    print("\n🎨 Step 2: Prompt Enhancement")
    print("-" * 30)
    
    # Enhance prompts for first few segments
    enhanced_prompts = []
    styles = [StylePreset.CINEMATIC_4K, StylePreset.GOLDEN_HOUR, StylePreset.DRAMATIC_LIGHTING]
    
    for i, segment in enumerate(segments[:6]):  # First 6 segments
        # Create basic visual description
        basic_desc = f"Scene showing {segment.text.split('.')[0].lower()}"
        
        # Enhance with rotating styles
        style = styles[i % len(styles)]
        enhanced = enhance_prompt(basic_desc, style.value)
        enhanced_prompts.append(enhanced)
        
        if i < 3:  # Show first 3
            print(f"   Segment {i+1}:")
            print(f"     Original: {basic_desc}")
            print(f"     Enhanced: {enhanced[:80]}...")
            print(f"     Style: {style.value}")
            print()
    
    print("\n📁 Step 3: Output Management")
    print("-" * 30)
    
    # Create project structure
    manager = create_project(
        topic="AI Revolution Demo",
        base_dir="demo_projects",
        total_segments=len(segments),
        target_duration=8.0,
        models_used={
            "text": "gemini-2.0-flash",
            "image": "imagen-3.0-generate-001"
        },
        generation_config={
            "style_presets": ["cinematic_4k", "golden_hour", "dramatic_lighting"],
            "quality": "ultra-high",
            "aspect_ratio": "16:9"
        }
    )
    
    print(f"✅ Created project: {manager.current_project_dir.name}")
    
    # Save first few segments
    saved_count = 0
    for i, (segment, enhanced_prompt) in enumerate(zip(segments[:6], enhanced_prompts)):
        segment_output = SegmentOutput(
            segment_id=segment.index,
            text=segment.text,
            enhanced_prompt=enhanced_prompt,
            duration=segment.duration,
            word_count=segment.word_count,
            status="completed"
        )
        
        paths = manager.save_segment_data(segment_output)
        saved_count += 1
        
        if i < 2:  # Show first 2
            print(f"   Saved segment {segment.index}:")
            print(f"     Text: {paths['text'].name}")
            print(f"     Prompt: {paths['prompt'].name}")
            print(f"     Metadata: {paths['metadata'].name}")
    
    # Update manifest
    manifest_path = manager.save_manifest({
        "demo_info": "Phase 4 demonstration",
        "segments_processed": saved_count,
        "enhancement_styles": [s.value for s in styles]
    })
    
    print(f"\n📋 Project Status:")
    status = manager.get_project_status()
    print(f"   Project ID: {status['project']['project_id'][:8]}...")
    print(f"   Total segments: {status['project']['total_segments']}")
    print(f"   Completed segments: {status['summary']['completed_segments']}")
    print(f"   Pending segments: {status['summary']['pending_segments']}")
    
    print("\n🎯 Step 4: Integration Summary")
    print("-" * 30)
    print(f"✅ Script successfully segmented into {len(segments)} parts")
    print(f"✅ {len(enhanced_prompts)} prompts enhanced with cinematic styles")
    print(f"✅ Project structure created with {saved_count} segments saved")
    print(f"✅ Manifest generated with complete metadata")
    
    print(f"\n📂 Output location: {manager.current_project_dir}")
    print(f"📄 Manifest file: {manifest_path.name}")
    
    print("\n" + "=" * 40)
    print("🎉 Phase 4 Demo Complete!")
    print("\n🚀 Core business logic is fully operational:")
    print("   • Script segmentation with precise timing")
    print("   • Cinematic prompt enhancement with multiple styles")
    print("   • Structured output management with metadata")
    print("   • End-to-end pipeline integration")
    
    print("\n✅ Phase 4 complete, ready for Phase 5.")
    
    return manager


if __name__ == "__main__":
    try:
        demo_phase4()
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)