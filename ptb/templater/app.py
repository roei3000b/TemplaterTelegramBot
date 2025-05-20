from flask import Flask, request, send_file, jsonify
import os
import tempfile
from templater import fill_template

app = Flask(__name__)

@app.route('/fill-template', methods=['POST'])
def fill_template_api():
    city = request.form.get('city')
    file = request.files.get('file')

    if not city or not file:
        return jsonify(error="Missing 'city' or 'file' parameter"), 400

    with tempfile.TemporaryDirectory() as temp_dir:
        input_path = os.path.join(temp_dir, file.filename)
        file.save(input_path)

        try:
            output_path = fill_template(city, input_path, temp_dir)
            output_filename = os.path.basename(output_path)
        except Exception as e:
            return jsonify(error=str(e)), 500

        return send_file(
            output_path,
            as_attachment=True,
            download_name=output_filename  # Flask 2.0+
        )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)