def make_exe(ctx):
    dist = ctx.default_python_distribution()

    policy = dist.make_python_packaging_policy()
    policy.include_stdlib = True
    policy.include_site_packages = True

    exe = dist.to_python_executable(
        name="clipfix",
        packaging_policy=policy,
    )

    exe.add_python_resources(exe.read_package_root("python"))

    exe.add_python_resources(
        exe.read_python_source(
            "from clipfix.main import main; import sys; sys.exit(main())"
        )
    )

    return exe

register_target("clipfix", make_exe)
