import os, glob, json
from omf import feeder

output_dir = "/Users/austinchang/pycharm/omf/omf/data/Component"
created = []
overwritten = []
not_overwritten = []
lacked_name = []

# TODO: improve comments, add tests with weird file names (e.g. file names with spaces, slashes, etc.)

def main(src_directory, overwrite=False):
	dictionaries = read_glm_files(src_directory)
	for d in dictionaries:
		create_components(d, overwrite)
	print_report(overwrite)

def read_glm_files(directory):
	""" Read each .glm file and return a dictionary of dictionaries
	"""
	os.chdir(directory)
	return [feeder.parse(file_path) for file_path in glob.glob("*.glm")]

def create_components(dictionary, overwrite):
	""" Create component.json files based on the provided dictionary.
	Existing component.json files with matching file names can be preserved or overwritten.
	"""
	for d in dictionary.values():
		object_type = d.get("object")
		if object_type is not None:
			# Add 'parent' attribute to houses and meters if they don't contain it
			if object_type in ["house", "meter"]:
				if d.get("parent") is None:
					d["parent"] = "null"
			# Remove quotes from the name is they existed
			name = d.get("name", "no_name").strip('"')
			if name != "no_name":
				d["name"] = name
			# I cannot have the "/" in a file name.
			name = name.replace("/", ",")
			file_name = object_type + "-" + name + ".json"
			if name == "no_name":
				lacked_name.append(file_name)
			path = os.path.join(output_dir, file_name)
			if not os.path.exists(path):
				created.append(file_name)
				with open(path, "w") as f:
					json.dump(d, f)
			elif not overwrite:
				not_overwritten.append(file_name)
			else:
				overwritten.append(file_name)
				with open(path, "w") as f:
					json.dump(d, f)

def print_report(overwrite):
	if len(lacked_name) > 0:
		print("\n********** The following objects lacked the 'name' property **********\n")
		for path in lacked_name:
			print(path)
	if overwrite:
		print("\n********** The following files were overwritten **********\n")
		for path in overwritten:
			print(path)
	else:
		print("\n********** The following files existed and were not overwritten **********\n")
		for path in not_overwritten:
			print(path)
	print("\n********** The following files were created **********\n")
	for path in created:
		print(path)

if __name__ == "__main__":
	main("/Users/austinchang/Desktop/testfiles/components", True)
