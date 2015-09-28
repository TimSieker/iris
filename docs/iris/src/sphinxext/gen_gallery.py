#
#    (C) Copyright 2012 MATPLOTLIB (vn 1.2.0)
#

'''
Generate a thumbnail gallery of examples.
'''

from __future__ import (absolute_import, division, print_function)

import os
import glob
import re
import warnings
import matplotlib.image as image


template = '''\
{{% extends "layout.html" %}}
{{% set title = "Thumbnail gallery" %}}


{{% block body %}}

<h3>Click on any image to see full size image and source code</h3>
<br/>

<ul>
<li><a class="reference internal" href="#">Gallery</a>
<ul>
{}
</ul>
</li>
</ul>

{}
{{% endblock %}}
'''

multiimage = re.compile('(.*?)(_\d\d){1,2}')


def make_thumbnail(args):
    image.thumbnail(args[0], args[1], 0.4)


def out_of_date(original, derived):
    return (not os.path.exists(derived) or
            os.stat(derived).st_mtime < os.stat(original).st_mtime)


def gen_gallery(app, doctree):
    if app.builder.name != 'html':
        return

    outdir = app.builder.outdir
    rootdir = 'examples'

    # Images we want to skip for the gallery because they are an unusual
    # size that doesn't layout well in a table, or because they may be
    # redundant with other images or uninteresting.
    skips = set([
        'mathtext_examples',
        'matshow_02',
        'matshow_03',
        'matplotlib_icon',
        ])

    thumbnails = {}
    rows = []
    random_image = []
    toc_rows = []

    link_template = ('<a href="{href}">'
                     '<img src="{thumb_file}" border="0"'
                     ' alt="{alternative_text}"/>'
                     '</a>')

    header_template = ('<div class="section" id="{}">'
                       '<h4>{}'
                       '<a class="headerlink" href="#{}"'
                       ' title="Permalink to this headline">&para;</a>'
                       '</h4>')

    toc_template = ('<li>'
                    '<a class="reference internal" href="#{}">{}</a>'
                    '</li>')

    random_image_content_template = '''
// This file was automatically generated by gen_gallery.py & should not be
// modified directly.

images = new Array();

{}

'''

    random_image_template = "['{thumbfile}', '{full_image}', '{link}'];"
    random_image_join = 'images[{}] = {}'

    dirs = ('General', 'Meteorology', 'Oceanography')

    for subdir in dirs:
        rows.append(header_template.format(subdir, subdir, subdir))
        toc_rows.append(toc_template.format(subdir, subdir))

        origdir = os.path.join(os.path.dirname(outdir), rootdir, subdir)
        if not os.path.exists(origdir):
            origdir = os.path.join(os.path.dirname(outdir), 'plot_directive',
                                   rootdir, subdir)
        thumbdir = os.path.join(outdir, rootdir, subdir, 'thumbnails')
        if not os.path.exists(thumbdir):
            os.makedirs(thumbdir)

        data = []

        for filename in sorted(glob.glob(os.path.join(origdir, '*.png'))):
            if filename.endswith('hires.png'):
                continue

            path, filename = os.path.split(filename)
            basename, ext = os.path.splitext(filename)
            if basename in skips:
                continue

            # Create thumbnails based on images in tmpdir, and place them
            # within the build tree.
            orig_path = str(os.path.join(origdir, filename))
            thumb_path = str(os.path.join(thumbdir, filename))
            if out_of_date(orig_path, thumb_path) or True:
                thumbnails[orig_path] = thumb_path

            m = multiimage.match(basename)
            if m is not None:
                basename = m.group(1)

            data.append((subdir, basename,
                         os.path.join(rootdir, subdir, 'thumbnails',
                                      filename)))

        for (subdir, basename, thumbfile) in data:
            if thumbfile is not None:
                anchor = os.path.basename(thumbfile)
                anchor = os.path.splitext(anchor)[0].replace('_', '-')
                link = 'examples/{}/{}.html#{}'.format(
                    subdir,
                    basename,
                    anchor)
                rows.append(link_template.format(
                    href=link,
                    thumb_file=thumbfile,
                    alternative_text=basename))
                random_image.append(random_image_template.format(
                    link=link,
                    thumbfile=thumbfile,
                    basename=basename,
                    full_image='_images/' + os.path.basename(thumbfile)))

        if len(data) == 0:
            warnings.warn('No thumbnails were found in {}'.format(subdir))

        # Close out the <div> opened up at the top of this loop.
        rows.append('</div>')

    # Generate JS list of images for front page.
    random_image_content = '\n'.join([random_image_join.format(i, line)
                                      for i, line in enumerate(random_image)])
    random_image_content = random_image_content_template.format(
        random_image_content)
    random_image_script_path = os.path.join(app.builder.srcdir,
                                            '_static',
                                            'random_image.js')
    with open(random_image_script_path, 'w') as fh:
        fh.write(random_image_content)

    content = template.format('\n'.join(toc_rows),
                              '\n'.join(rows))

    # Only write out the file if the contents have actually changed.
    # Otherwise, this triggers a full rebuild of the docs.

    gallery_path = os.path.join(app.builder.srcdir,
                                '_templates',
                                'gallery.html')
    if os.path.exists(gallery_path):
        with open(gallery_path, 'r') as fh:
            regenerate = fh.read() != content
    else:
        regenerate = True
    if regenerate:
        with open(gallery_path, 'w') as fh:
            fh.write(content)

    for key in app.builder.status_iterator(thumbnails.iterkeys(),
                                           'generating thumbnails... ',
                                           length=len(thumbnails)):
        image.thumbnail(key, thumbnails[key], 0.3)


def setup(app):
    app.connect('env-updated', gen_gallery)
