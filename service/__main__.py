import bottle

from config_finder import cfg

from handlers import (
    handle_branch_commit,
    handle_build,
)

commit_path = "/commit/<{}>/<{}>/<{}>/<{}>".format(
    "repo_name",
    "feature_name",
    "branch_name",
    "commit_hash",
)
build_path = "/build/<commit_hash>/<image_name>"

bottle.route(commit_path, ["GET"], handle_branch_commit)
bottle.route(build_path, ["GET"], handle_build)

debug = cfg('debug', "false") == "true"
print("running herd api, debug? {}".format(debug))
bottle.run(host='0.0.0.0', port='8000', debug=debug)
