GL_VERSIONS = {
    'core': [
        (4, 5),
        (4, 4),
        (4, 3),
        (4, 2),
        (4, 1),
        (4, 0),
        (3, 3),
        (3, 2),
        (3, 1),
        (3, 0),
        (2, 1),
        (2, 0),
        (1, 5),
        (1, 4),
        (1, 3),
        (1, 2),
        (1, 1),
        (1, 0)
    ],
    'ES': [
        (3, 1),
        (3, 0),
        (2, 0),
        (1, 1),
        (1, 0)
    ]
}

def get_version_range(profile, min_version, max_version):
    all_versions = GL_VERSIONS[profile]
    versions = all_versions[all_versions.index(max_version):all_versions.index(min_version)]
    return [(profile, major, minor) for major, minor in versions]
