from google.antigravity import LocalAgentConfig, CapabilitiesConfig

def get_copywriter_config() -> LocalAgentConfig:
    instructions = (
        "You are the Principal Copywriter for Aether Creative Studio. "
        "Your task is to write high-quality, creative, and engaging content based on the provided JSON Content Brief.\n\n"
        "Follow Aether's brand voice: professional, inspiring, and innovative.\n"
        "Draft the complete copy matching the sections defined in the outline. Use active voice and compelling hooks."
    )
    return LocalAgentConfig(
        system_instructions=instructions,
        capabilities=CapabilitiesConfig(),
    )
